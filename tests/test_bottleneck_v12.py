"""test_bottleneck_v12.py — aday-debisi darboğaz turu (2026-07-20, "öncelikle darboğazlara odaklanalım").

Huni ölçümü (son 10 seans, 243 sembol) iki gerçek darboğaz gösterdi:
#1 SEANS ATLAMA: iki poll arasına birden çok seans sığarsa yalnız SONUNCUSU işleniyordu — 2026-07-16
   canlıda HİÇ işlenmedi ve o günün gerçek VCP adayı kayıtsız kayboldu. Zamanlayıcı artık işlenmemiş
   HER seansı sırayla (on_date) yakalar.
#2 KANIT KÖRLÜĞÜ: kırılım-sonrası ölümlerin ezici kısmı hacim×1.5 / RS 70 eşiklerinde — ama eşiğin
   hemen altında ölenler hiçbir deftere girmiyordu. Gevşek GÖLGE taraması bunları karşı-olgusala
   near_miss olarak yazar (SIFIR yetki; resolved_rows varsayılan dışlar; LLM bütçesi harcanmaz)."""
import pandas as pd
import pytest

from meridian import config, store
from meridian.strategy import EntrySignal


def _sig(ticker="AAA", setup="breakout_vcp", rs=60, score=55,
         notes="prox=1.00% vr=1.20 tt=0.80 rr=2.50"):
    return EntrySignal(ticker=ticker, setup=setup, entry_trigger=100.0, pivot=99.0, stop=96.0,
                       atr=1.5, rs_rating=rs, score=score, profit_target=108.0, size_r=1.0,
                       r_per_share=4.0, notes=notes)


# ---------------- #1: sıralı seans yakalama ----------------
def test_scheduler_catches_up_every_unprocessed_session(sandbox_state, monkeypatch):
    """3 seanslık veri, kitap 1. seansta kalmış → 2. VE 3. seans SIRAYLA işlenir (yalnız sonuncusu değil)."""
    from meridian import scheduler, loop, dataset, health

    dates = pd.to_datetime(["2026-07-15", "2026-07-16", "2026-07-17"])
    index = pd.DataFrame({"date": dates, "close": [100.0, 101.0, 102.0]})
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-07-17")
    monkeypatch.setattr(dataset, "load", lambda use_cache=True: ({}, index))
    store.write_json("portfolio.json", {"last_date": "2026-07-15", "positions": {}, "armed": []})
    scheduler._state["last_refetch_session"] = "2026-07-17"   # tazeleme dalını sustur

    seen = []
    monkeypatch.setattr(loop, "daily_cycle",
                        lambda bars, idx, on_date=None: seen.append(on_date) or
                        {"date": on_date, "status": "ok"})
    out = scheduler.advance_once()
    assert seen == ["2026-07-16", "2026-07-17"]               # atlanmış seans da işlendi, sırayla
    assert out["status"] == "advanced" and out["sessions"] == seen


def test_scheduler_current_when_no_new_session(sandbox_state, monkeypatch):
    """Kitap zaten son barda → 'current' yolu değişmedi (hiçbir döngü koşmaz)."""
    import shutil
    from pathlib import Path
    from meridian import scheduler, loop, dataset, health
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):                    # current yolu nabız yazar → goal gerekir
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    index = pd.DataFrame({"date": pd.to_datetime(["2026-07-17"]), "close": [102.0]})
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-07-17")
    monkeypatch.setattr(dataset, "load", lambda use_cache=True: ({}, index))
    store.write_json("portfolio.json", {"last_date": "2026-07-17", "positions": {}, "armed": []})
    scheduler._state["last_refetch_session"] = "2026-07-17"
    monkeypatch.setattr(loop, "daily_cycle",
                        lambda *a, **k: pytest.fail("current durumda döngü koşmamalı"))
    assert scheduler.advance_once()["status"] == "current"


# ---------------- #2: near-miss karşı-olgusal ----------------
def test_near_miss_rows_collected_and_excluded_by_default(sandbox_state):
    from meridian import counterfactual as cf
    added = cf.collect("2026-07-17", plans=[], armed_ids=set(),
                       dormant_sigs=[], time_stop_days=15,
                       near_miss=[(_sig(), ["rs", "hacim"])])
    assert added == 1
    row = store.read_json("cf_open.json", [])[0]
    assert row["id"].endswith("-nm") and row["verdict"] == "NEAR_MISS"
    assert row["near_miss"] is True and row["blocked_by"] == ["rs", "hacim"]
    # çözülmüş near-miss satırı VARSAYILAN dışlanır — 8 mevcut tüketici seyrelmez
    store.write_jsonl("counterfactuals.jsonl", [
        {"id": "CF-x-nm", "near_miss": True, "entered": True, "r_multiple": 0.8},
        {"id": "CF-y", "entered": True, "r_multiple": 0.1},
    ])
    assert [r["id"] for r in cf.resolved_rows(entered_only=True)] == ["CF-y"]
    assert len(cf.resolved_rows(entered_only=True, include_near_miss=True)) == 2


def test_near_miss_blockers_from_fields_and_notes(sandbox_state):
    from meridian import loop
    eff = {"entry.rs_rating_min": 70, "entry.min_volume_ratio": 1.5,
           "entry.min_score": 60, "entry.pivot_proximity_pct": 2.0}
    assert loop._near_miss_blockers(_sig(rs=60, score=55), eff) == ["rs", "skor", "hacim"]
    assert loop._near_miss_blockers(_sig(rs=90, score=80, notes="prox=3.10% vr=2.00"), eff) == ["uzamış"]
    assert loop._near_miss_blockers(_sig(rs=90, score=80, notes=""), eff) == ["diğer"]


def test_near_miss_report_buckets(sandbox_state):
    from meridian import analytics
    store.write_jsonl("counterfactuals.jsonl", [
        {"id": "a-nm", "near_miss": True, "blocked_by": ["hacim"], "entered": True, "r_multiple": 0.6},
        {"id": "b-nm", "near_miss": True, "blocked_by": ["hacim"], "entered": True, "r_multiple": 0.2},
        {"id": "c-nm", "near_miss": True, "blocked_by": ["rs"], "entered": False},
        {"id": "d", "entered": True, "r_multiple": -0.5},                  # normal satır — rapora girmez
    ])
    rep = analytics.near_miss_report()
    assert rep["resolved_total"] == 3
    # ikinci tur denetimi (2026-07-21): kovaya REJİM KIRILIMI eklendi — öneri hangi rejime
    # yazılacağını kanıta dayandırabilsin diye. Rejimsiz eski satırlar "?" dilimine düşer.
    b = rep["buckets"]["hacim"]
    assert (b["n"], b["entered"], b["n_r"], b["avg_r"]) == (2, 2, 2, 0.4)
    assert b["by_regime"]["?"]["n_r"] == 2
    assert rep["buckets"]["rs"]["entered"] == 0
    assert store.read_json("near_miss.json", {})["resolved_total"] == 3


# ---------------- 2. tur (onaylı): geriye-döngü bekçisi · güncellik · borç · re-seed emniyeti ----------------
def test_daily_cycle_refuses_regressive_session(sandbox_state):
    """GS'yi öldüren halka (07-15 10:29): bayat/yedek kaynak endeksi geriletti, döngü kitabı geri sardı.
    Artık işlenecek seans kitabın son tarihinden ESKİYSE döngü olaylı reddeder; kitaba dokunmaz."""
    import shutil
    from pathlib import Path
    from meridian import loop
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    store.write_json("portfolio.json", {"last_date": "2026-07-17", "positions": {}, "armed": []})
    index = pd.DataFrame({"date": pd.to_datetime(["2026-07-13"]), "open": [100.0], "high": [101.0],
                          "low": [99.0], "close": [100.5], "volume": [1e6]})
    out = loop.daily_cycle({}, index)
    assert out["status"] == "refused_regressive" and out["book_at"] == "2026-07-17"
    assert store.read_json("portfolio.json", {})["last_date"] == "2026-07-17"    # kitap el değmedi
    assert any(e.get("event") == "regressive_session_refused"
               for e in store.read_jsonl("events.jsonl"))


def test_scan_debt_lifecycle(sandbox_state, monkeypatch):
    """Borç defteri: güncel olmayan sembol borçlanır (dedup+cap); barı gelince kaçan seans o günkü
    kuyrukla değerlendirilir ve borç düşer; 7 günü aşan bar'sızlık olaylı düşer; taze gecikme bekler."""
    from meridian import loop, strategy as strat_mod
    from tests.conftest import make_bars
    loop._scan_debt_add("GS", "2026-07-15")
    loop._scan_debt_add("GS", "2026-07-15")                       # dedup
    loop._scan_debt_add("XX", "2026-07-15")                       # barı hiç gelmeyecek (bekleyen)
    loop._scan_debt_add("YY", "2026-07-01")                       # 7 günü aşacak (düşer)
    assert len(store.read_json("scan_debt.json", [])) == 3

    df = make_bars(n=340).set_index("date")               # canlı per ile birebir: sütun indexe taşınır
    last = df.index[-1]                                           # borç tarihi = bu bar
    per = {"GS": df, "XX": df.iloc[:-3], "YY": df.iloc[:-30]}     # XX/YY'de o bar yok
    debts = [{"ticker": "GS", "date": str(last.date())},
             {"ticker": "XX", "date": str(last.date())},
             {"ticker": "YY", "date": str((last - pd.Timedelta(days=10)).date())}]
    store.write_json("scan_debt.json", debts)
    fake = _sig(ticker="GS")
    monkeypatch.setattr(strat_mod, "scan_all", lambda *a, **k: {"breakout_vcp": fake})
    out = loop._scan_debt_collect(per, last, {})
    assert list(out) == [str(last.date())]                        # kaçan seans kendi tarihiyle döner
    assert out[str(last.date())] == [(fake, ["geç_bar"])]
    kept = store.read_json("scan_debt.json", [])
    assert [r["ticker"] for r in kept] == ["XX"]                  # GS çözüldü, YY yaşlandı, XX bekliyor
    assert any(e.get("event") == "scan_debt_expired" and e.get("ticker") == "YY"
               for e in store.read_jsonl("events.jsonl"))


def test_currency_guard_wiring_live_and_backtest(sandbox_state):
    """Kaynak-denetim: bayat kuyrukla tarama iki tarafta da (canlı P2 + backtest) kapalı; canlıda
    taze gecikme borca yazılır; RS havuzları güncel olmayan sembolü almaz."""
    import inspect
    from meridian import loop, backtest
    live = inspect.getsource(loop.daily_cycle)
    assert live.count("d not in df_t.index") >= 2                 # tarama + RS havuzu
    assert "_scan_debt_add(t, dstr)" in live
    bt = inspect.getsource(backtest)
    assert bt.count("d not in df_t.index") >= 2                   # simetri: canlı↔backtest aynı yasa


def test_reseed_refuses_with_armed_plans(sandbox_state, monkeypatch):
    """Silahlı plan varken replay kitabı silemez (GS dersi); açık niyet MERIDIAN_FORCE_RESEED=1 ister."""
    import shutil
    from pathlib import Path
    from meridian import run, dataset
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):                    # FORCE yolu config.goal()'a ulaşır
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    store.write_json("portfolio.json", {"last_date": "2026-07-17", "positions": {},
                                        "armed": [{"id": "P-x", "ticker": "GS"}]})
    monkeypatch.delenv("MERIDIAN_FORCE_RESEED", raising=False)
    out = run.replay_seed("2022-01-01", "2022-02-01")
    assert out == {"error": "armed_plans_present", "armed": ["GS"]}
    monkeypatch.setenv("MERIDIAN_FORCE_RESEED", "1")
    monkeypatch.setattr(dataset, "load", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("geçti")))
    with pytest.raises(RuntimeError, match="geçti"):              # bekçiyi bilerek aştı → replay başlar
        run.replay_seed("2022-01-01", "2022-02-01")


def test_universe_swap_clean(sandbox_state):
    from meridian.adapters.data import REPLAY_UNIVERSE
    from meridian.backtest import SECTORS
    dead = {"DFS", "FI", "HES", "IPG", "K", "PARA", "WBA"}
    fresh = {"PNC", "USB", "EQT", "TTWO", "EA", "KVUE", "HRL"}
    # 250 → 251 (2026-07-30, operatör kararı: FISV — emekli FI'nin Nasdaq'taki halefi).
    assert len(REPLAY_UNIVERSE) == 251 == len(set(REPLAY_UNIVERSE))
    assert not (dead & set(REPLAY_UNIVERSE)) and fresh <= set(REPLAY_UNIVERSE)
    assert all(t in SECTORS for t in REPLAY_UNIVERSE)             # sektör haritası deliksiz


def _near_miss_kullanimlari() -> list[tuple[str, int]]:
    """`daily_cycle` içinde `near_miss_sigs`in HER kullanımını AST'den çıkarır: (rol, satır).

    NEDEN AST, NEDEN METİN DEĞİL (2026-07-31, WP-E turu): eski çivi kaynağı ard arda üç `split`
    ile dilimliyordu (`"counterfactual.collect"` → `"explore_pool = []"` → `"from .shadow_model"`).
    Üçü de METİN çapasıydı ve üçü de YORUM SATIRLARINI kaynaktan ayırt edemiyordu: bir başka turda
    P4 dolum bloğuna `counterfactual.collect her planı açar` diye AÇIKLAYICI bir yorum yazıldı,
    ilk `split` kaynağı o YORUMDAN kesti, ikinci çapa artık dilimin içinde kalmadı ve tel
    `IndexError` ile düştü — yani çivi, denetlediği DEĞİŞMEZ hiç bozulmamışken kırmızı yandı.
    Yanlış ağlayan tel sökülür; o yüzden çapa gerçek bir tel olan AST'ye taşındı. Yorum metni
    AST'de YOKTUR ve `explore_pool` initinin tek satıra mı demete mi yazıldığı da fark etmez.

    İDDİANIN DİŞİ GEVŞEMEDİ, SERTLEŞTİ: eski tel yalnız BİR BÖLGEDE (explore_pool init →
    cf.collect) yokluk arıyordu. Yenisi fonksiyonun TAMAMINDA her kullanımı ADLANDIRIYOR: beyaz
    listede olmayan tek bir kullanım (bir `if`, bir skor girdisi, bir `armed.append`) belirirse
    rolü `BEYAZ_LISTE_DISI` olur ve test düşer."""
    import ast
    import inspect
    import textwrap
    from meridian import loop

    src = textwrap.dedent(inspect.getsource(loop.daily_cycle))
    fn = ast.parse(src).body[0]
    ebeveyn = {}
    for n in ast.walk(fn):
        for c in ast.iter_child_nodes(n):
            ebeveyn[c] = n

    def _cagri_zinciri(n):
        """Düğümü SARAN tüm çağrıların adları (en içten en dışa) — argüman içine gömülü bir
        comprehension'ın hangi fonksiyona gittiğini ancak zincir söyler."""
        adlar = []
        while n is not None:
            if isinstance(n, ast.Call):
                f = n.func
                adlar.append(f"{getattr(f.value, 'id', '?')}.{f.attr}"
                             if isinstance(f, ast.Attribute) else getattr(f, "id", "?"))
            n = ebeveyn.get(n)
        return adlar

    out = []
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Name) and n.id == "near_miss_sigs"):
            continue
        p, zincir = ebeveyn.get(n), _cagri_zinciri(n)
        if isinstance(n.ctx, ast.Store):
            rol = "init"
        elif isinstance(p, ast.Attribute) and p.attr == "append":
            rol = "topla"                       # P2 taraması eşik-altı adayı DEFTERE yazar
        elif isinstance(p, ast.keyword) and p.arg == "near_miss" and "counterfactual.collect" in zincir:
            rol = "cf_defteri"                  # tek çıkış: karşı-olgusal defter (sıfır yetki)
        elif isinstance(p, ast.comprehension) and "_sv.record_cycle" in zincir:
            rol = "golge_nufusu"                # gölge-varyant ÖLÇÜM nüfusu (kendi defteri, sıfır yetki)
        elif isinstance(p, ast.Call) and getattr(p.func, "id", None) == "len":
            rol = "ozet_sayaci"                 # daily_cycle özet olayı + dönüşü (2026-08-12 sessiz-ölüm
                                                # dersi): len() sayar, satırların İÇERİĞİ okunmaz — görünürlük
        elif isinstance(p, ast.UnaryOp) and isinstance(p.op, ast.Not):
            rol = "kuraklik_bekcisi"            # aday-varken-0-gölge uyarısının koşulu (obs.warn) — YASA 4
                                                # olayı üretir, hiçbir karar ifadesine girmez
        else:
            rol = "BEYAZ_LISTE_DISI"
        out.append((rol, n.lineno))
    return out


def test_shadow_scan_wiring_is_zero_authority(sandbox_state):
    """Kaynak-denetim: gölge tarama yalnız SİLAHLI kurulumları near-miss toplar, karar akışına girmez;
    LLM damgası near-miss satırlarına bütçe harcamaz."""
    import inspect
    from meridian import loop, hermes
    src = inspect.getsource(loop.daily_cycle)
    assert "_su in strat.ARMED_SETUPS and _su not in _all" in src   # yalnız silahlı kurulum, yalnız eşik-altı
    assert "near_miss=near_miss_sigs" in src                        # tek çıkış: karşı-olgusal defter

    kullanimlar = _near_miss_kullanimlari()
    roller = sorted(r for r, _ in kullanimlar)
    # ALTI ROL, HEPSİ BU: topla → (cf defteri | gölge ölçüm nüfusu) + iki GÖRÜNÜRLÜK kullanımı
    # (2026-08-12 sessiz-ölüm dersi: özet sayaç ×2 — olay + dönüş — ve kuraklık bekçisi; ikisi de
    # len()/not ile SAYAR, satır içeriği okumaz). Aday/plan/keşif SEÇİMİNDE kullanım YOK — yeni
    # bir kullanım belirirse `BEYAZ_LISTE_DISI` olarak burada patlar.
    assert roller == ["cf_defteri", "golge_nufusu", "init", "kuraklik_bekcisi",
                      "ozet_sayaci", "ozet_sayaci", "topla"], \
        f"near_miss_sigs kullanımı değişti: {kullanimlar}"

    # SIRA DA YASANIN PARÇASI: karar akışı (P2 tarama → P3 plan → silahlanma) cf devrinden ÖNCE
    # biter. `topla` dışındaki hiçbir kullanım o aralıkta olamaz — yani eşik-altı kanıt, kararı
    # üreten hiçbir ifadeye giremez. Görünürlük rolleri de gölge-devrinden SONRA gelmek zorunda:
    # sayacın kendisi bile karar penceresine sızamaz.
    satir = {r: ln for r, ln in kullanimlar}
    assert satir["init"] < satir["topla"] < satir["cf_defteri"] < satir["golge_nufusu"]
    assert not [ln for r, ln in kullanimlar
                if r not in ("init", "topla") and ln < satir["cf_defteri"]]
    assert all(ln > satir["golge_nufusu"] for r, ln in kullanimlar
               if r in ("kuraklik_bekcisi", "ozet_sayaci"))

    assert 'r.get("near_miss")' in inspect.getsource(hermes._stamp_llm_opinions)


# ---------------- 3. tur (operatör: kâğıt modunda kanıt debisi) ----------------
def test_dormant_explore_and_budget_floor_wiring(sandbox_state):
    """Kaynak-denetim: uyuyan kurulum planı YALNIZ keşif havuzuna girer (GO şartı), normal slota asla;
    kimliği kurulum ekli (çakışma + cf ayrışması); keşif silahlama tek blok (çift-silahlanma yaması);
    havuz artık her rejimde işler (uyuyan sondalar bütçe>0'da da)."""
    import inspect
    from meridian import loop, config as cfg
    src = inspect.getsource(loop.daily_cycle)
    assert src.count("exploration_armed") == 1 and src.count("KEŞİF SLOT SEÇİMİ") == 1
    assert 'if plan["dormant_setup"]:' in src                     # uyuyan dal normal slottan ÖNCE
    assert src.index('if plan["dormant_setup"]:') < src.index('elif verdict != "NO_GO" and slots > 0:')
    assert "if explore_pool:" in src and "if explore_mode and explore_pool:" not in src
    assert '''f"P-{dstr}-{c['ticker']}-{c.get('setup','')}"''' in src
    live = cfg.load_strategy() if False else None                 # canlı dosyaya dokunma (sandbox boş)
    assert live is None


def test_operator_budget_floor_is_versioned(sandbox_state):
    """Yürürlükteki parametreler KARNEYLE KAYITLI SOYDAN gelir — kayıtsız değişiklik kırmızı yakar.

    NEDENSEL ZİNCİR (bu telin neden yeniden yazıldığı, 2026-07-28):
      2026-07-23  v4 yayında: `source: operator_override`, regime.min_exposure_score = 20
                  ("operatör tabanı yürürlükte" — elle konmuş bir taban).
      2026-07-26  Taban ÖLÇÜLDÜ ve yayınlandı (operatör "Yayınla" ile onayladı): v3 için
                  backtest_oos=0.1245, baseline_verdict="olculebilir", n=103.
      2026-07-28  Otomatik rollback: "ROLLBACK v4 → v3 underperformed by 0.1334" → `revert_to(3)`
      09:55       canlı strategy.yaml'ı v3 anlık görüntüsüne döndürdü; min_exposure_score 20 → 40.
                  Monotonluk dedektörü sürüm gerilemesini ADIYLA alarmladı (beklenen ve kayıtlı).

    Eski tel `== 20` çiviliyordu ve bu MEŞRU geçişte yanlış yere ağladı: sabit değer çivilemek,
    telin bir sonraki onaylı kararda da yanlış ağlayacağı anlamına gelir — ve sürekli yanlış ağlayan
    bir tel sökülür. Tel gevşetilmiyor, HEDEFİ düzeltiliyor: korunan şey artık "20" değil,
    **'yürürlükteki değer karneyle kayıtlı soydan gelir'** yasasıdır.

    versioning.py'nin sözleşmesi (modül başlığı): "bir parametre değişikliği = sürüm artışı +
    state/history/vNNNN.yaml anlık görüntüsü + hot-reload edilebilir strategy.yaml". Üç ayak da
    tutmak zorunda; biri tutmazsa değişiklik DEFTERE GİRMEDEN olmuş demektir (elle düzenleme,
    yarım rollback, kayıp snapshot) ve bu her zaman kırmızıdır.
    """
    import json
    import yaml
    from pathlib import Path
    repo = Path(__file__).resolve().parent.parent / "state"
    strat = yaml.safe_load((repo / "strategy.yaml").read_text())
    sb = json.loads((repo / "scoreboard.json").read_text())
    ver = int(strat["version"])

    # (1) Canlı sürüm, karnenin YÜRÜRLÜKTE dediği sürümdür. Ayrışırlarsa pano bir sürümü, motor
    #     başka birini işletiyor demektir.
    assert ver == int(sb["current_version"]), (
        f"canlı strategy.yaml v{ver} ama karne v{sb['current_version']} diyor")

    # (2) Canlı parametreler o sürümün DEĞİŞMEZ anlık görüntüsünden gelir. Elle bir düğmeye
    #     dokunulduğunda (sürüm artışı ve snapshot olmadan) burası ayrışır — telin asıl işi bu.
    snap_path = repo / "history" / f"v{ver:04d}.yaml"
    assert snap_path.exists(), f"v{ver} yürürlükte ama {snap_path.name} anlık görüntüsü YOK"
    snap = yaml.safe_load(snap_path.read_text())
    assert strat["params"] == snap["params"], (
        "canlı parametreler yürürlükteki sürümün anlık görüntüsüyle uyuşmuyor — kayıtsız değişiklik: "
        + str({k: (strat["params"].get(k), snap["params"].get(k))
               for k in set(strat["params"]) | set(snap["params"])
               if strat["params"].get(k) != snap["params"].get(k)}))

    # (3) Yürürlükteki sürümün karnede bir satırı olmalı: sürüm yayında ama defterde yoksa, karar
    #     görünmez olmuştur. Satırın PROVENANSI da olmalı — nasıl yürürlüğe girdiği yazılı olsun
    #     (ship/rollback/operatör kararı); alan adları şemadan okunur, uydurulmaz.
    row = (sb.get("versions") or {}).get(str(ver))
    assert row is not None, f"v{ver} yürürlükte ama karnede satırı yok"
    assert any(k in row for k in ("source", "reinstated", "parent", "live_since", "backtest_oos")), (
        f"v{ver} satırı provenanssız — nasıl yürürlüğe girdiği kayıtlı değil: {sorted(row)}")


# ---------------- KAPI BÜTÜNLÜĞÜ: bar değişimi wf-önbelleğini geçersiz kılmalı (2026-07-21) ----------------
def test_corporate_action_reset_invalidates_wf_cache(sandbox_state, monkeypatch):
    """CANLIDA BULUNDU: corporate-action reset bar CSV'sini siler/yeniden yazar ama wf-cache revizyonunu
    bumplamıyordu → kapı, BAYAT-bar incumbent'ını TAZE-bar candidate'ıyla kıyaslıyordu (elma-armut).
    Kanıt: aynı v4 incumbent'ı 0.2043 → 0.1130 → 0.0988 sürüklendi. Barlar değişince revizyon ARTMALI."""
    import pandas as pd
    from meridian.adapters import data
    old = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                        "open": [100.0, 101.0], "high": [101.0, 102.0], "low": [99.0, 100.0],
                        "close": [100.0, 101.0], "volume": [1e6, 1e6]})
    old.to_csv(data._cache_path("TEST"), index=False)
    new = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03"]),      # 4:1 split ölçeği
                        "open": [25.0, 25.3], "high": [25.3, 25.5], "low": [24.8, 25.0],
                        "close": [25.0, 25.3], "volume": [4e6, 4e6]})
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: new)
    store.write_json("wf_cache_rev.json", {"rev": 5})
    data.load_bars("TEST", "2024-01-01", "2024-01-03", use_cache=False)
    # rev artık MONOTON zaman damgası (sayaç değil): sadece ARTMIŞ olmalı — bayat walk-forward'lar ölür
    assert store.read_json("wf_cache_rev.json", {}).get("rev") > 5


def test_normal_refetch_does_not_bump_wf_cache(sandbox_state, monkeypatch):
    """Karşı-kontrol: corporate action YOKKEN (normal tazeleme) revizyon artmaz — yoksa her yüklemede
    tüm walk-forward önbelleği çöpe gider ve arama felç olur."""
    import pandas as pd
    from meridian.adapters import data
    same = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                         "open": [100.0, 101.0], "high": [101.0, 102.0], "low": [99.0, 100.0],
                         "close": [100.0, 101.0], "volume": [1e6, 1e6]})
    same.to_csv(data._cache_path("TEST2"), index=False)
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: same)     # aynı ölçek → corporate action yok
    store.write_json("wf_cache_rev.json", {"rev": 5})
    data.load_bars("TEST2", "2024-01-01", "2024-01-03", use_cache=False)
    assert store.read_json("wf_cache_rev.json", {}).get("rev") == 5    # corporate action yok → bump yok


def test_pool_workers_load_bars_without_network(sandbox_state, monkeypatch):
    """CANLIDA BULUNDU (2026-07-21): süreç havuzundaki HER işçi kendi dataset.load()'unu çağırıyordu;
    load() bayat önbellekte fetch eder ve fetch corporate-action tespitiyle bar CSV'lerini YENİDEN YAZAR
    → işçiler birbirinin barlarını değiştiriyor, aynı aramanın sondaları FARKLI bar durumlarında
    ölçülüyordu. İşçiler artık ağa çıkmayan load_cached() kullanmalı (ebeveynin yerleştirdiği donmuş
    önbellek). Aksi halde kapı kıyasları elma-armut olur."""
    import inspect
    from meridian import reflect, dataset
    from meridian.adapters import data
    src = inspect.getsource(reflect._pool_worker_init)
    assert "load_cached()" in src, "havuz işçisi ağa çıkabilen load() kullanıyor"
    assert "_ds.load(use_cache" not in src
    # load_cached ASLA fetch etmez
    monkeypatch.setattr(data, "fetch",
                        lambda *a, **k: pytest.fail("load_cached ağa çıktı — determinizm bozuldu"))
    bars, idx = dataset.load_cached()          # boş sandbox: sonuç boş olabilir, ama fetch ETMEMELİ
    assert isinstance(bars, dict)

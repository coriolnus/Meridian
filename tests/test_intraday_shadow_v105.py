"""test_intraday_shadow_v105.py — FAZ 4B GÖLGE MODU: KARAR ÖLÇÜLÜYOR, YETKİ VERİLMİYOR (2026-07-27).

Faz 4a "tetik kesildi mi?"yi ölçüyordu; cevaplayamadığı soru "kesildiğinde NE OLURDU?"ydı. Bir eşik
geçişi tek başına karar DEĞİLDİR — kapılar, boyutlandırma, likidite tavanı ve gap korumaları emri
tümüyle iptal edebilir. Bu testler gölge katmanının iki sözünü kilitler:

  (1) KARAR EOD İLE AYNI KODDAN ÇIKAR. qty/risk ikinci bir kopyayla değil `broker.fill_entry` ile
      hesaplanır; ADV penceresi EOD'nin kullanacağı 20 barın AYNISIDIR. Ayrışan bir kopya, gölge
      defterini EOD'yi değil KENDİNİ ölçer hâle getirirdi ve bu hiçbir yerde görünmezdi.
  (2) HİÇBİR YETKİ YOK. Tek yazılan dosya gölge defteridir: portfolio.json'a, INTRADAY_ARM'a,
      hiçbir broker/alpaca yoluna dokunulmaz. "Ölçüyorum" diyen bir katmanın sessizce durum
      değiştirmesi, bu deponun kovaladığı hata sınıfının en pahalısı olurdu.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest

from meridian import barclock, config, intraday_shadow, store
from meridian.broker import PaperBroker, Position, derisk_mult

SRC = pathlib.Path("meridian/intraday_shadow.py")
APP_JS = pathlib.Path("meridian/web/app.js")

_SIMDI = dt.datetime(2026, 7, 27, 15, 40, 0, tzinfo=dt.timezone.utc)   # RTH içi (11:40 ET)
_SEANS = "2026-07-27"


@pytest.fixture
def saat(monkeypatch):
    monkeypatch.setattr(barclock, "now", lambda: _SIMDI)
    intraday_shadow.reset_dedup()
    yield _SIMDI
    intraday_shadow.reset_dedup()


def _bar(o=100.0, h=112.0, l=99.0, c=110.0, dakika_once=2.0) -> dict:
    t = _SIMDI - dt.timedelta(minutes=dakika_once)
    return {"t": t.strftime("%Y-%m-%dT%H:%M:00Z"), "o": o, "h": h, "l": l, "c": c, "v": 5000.0}


def _plan(**kw) -> dict:
    p = {"id": "P-2026-07-27-AAA", "ticker": "AAA", "side": "long", "entry_trigger": 105.0,
         "stop": 95.0, "profit_target": 130.0, "size_r": 1.0, "r_multiple_expected": 2.5,
         "regime_at_plan": "chop", "strategy_version": 4, "setup": "breakout_vcp", "score": 80}
    p.update(kw)
    return p


def _saglikli_state(state, *, halted=False, data_halt=False, day_pnl_pct=0.0,
                    positions=None, realized_pnl=0.0, peak=100_000.0):
    """Kapıların HEPSİ ölçülebilir olsun: gölge, kaynağı olmayan kapıyı fail-closed sayar.

    Sermaye `realized_pnl` ile sürülür, `cash` ile DEĞİL: `PaperBroker.equity()` tanımı
    `start_equity + realized_pnl`tir (nakit bakiyesi değil). Drawdown senaryosunu nakit üzerinden
    kurmak testi sessizce etkisiz bırakırdı — ilk yazımda tam olarak bu oldu."""
    store.write_json("portfolio.json", {"cash": 100_000.0 + realized_pnl, "realized_pnl": realized_pnl,
                                        "last_id": 0,
                                        "positions": positions or {}, "armed": [],
                                        "peak_equity": peak, "day_start_equity": 100_000.0})
    store.write_json("heartbeat.json", {"ts": "2026-07-27T13:56:11+00:00", "day_pnl_pct": day_pnl_pct})
    store.write_json("data_quality.json", {"date": "2026-07-24", "data_halt": data_halt})
    if halted:
        (state / "HALT").write_text("test")


def _gunluk_barlar(state, ticker="aaa", n=40, hacim=800_000.0):
    """Günlük EOD CSV — son satır DÜN (seans içi gerçeklik: bugünün günlük barı henüz yok)."""
    import pandas as pd
    dates = pd.bdate_range(end="2026-07-24", periods=n).strftime("%Y-%m-%d").tolist()
    satir = ["date,open,high,low,close,volume"]
    for i, d in enumerate(dates):
        satir.append(f"{d},100,101,99,100,{hacim + i}")
    (state / "bars" / f"{ticker}.csv").write_text("\n".join(satir) + "\n")


# =================================================================================================
# 1) BOYUTLANDIRMA KİMLİĞİ — aynı kodun çağrıldığının kanıtı
# =================================================================================================
def test_qty_ve_risk_scratch_broker_fill_entry_ile_AYNI(sandbox_state, saat):
    """Gölge, boyutlandırmayı yeniden yazsaydı iki hesap zamanla ayrışırdı ve ayrıştığı gün defter
    EOD'yi değil kendini ölçüyor olurdu. Kimlik burada çivilenir."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    plan, bar = _plan(), _bar(o=100.0)

    satir = intraday_shadow.record(plan, bar, _SIMDI)

    assert satir["status"] == "would_submit"
    # Bağımsız scratch broker: aynı girdiler, aynı fonksiyon.
    goal = config.goal()
    b = PaperBroker(100_000.0, float(goal.get("slippage_bps", 5)), float(goal.get("commission_per_share", 0.0)))
    b.cash, b.realized_pnl = 100_000.0, 0.0
    beklenen = b.fill_entry(plan, satir["sim_price"], _SIMDI.isoformat(), b.equity(),
                            size_mult=derisk_mult(b.equity(), 100_000.0),
                            adv=intraday_shadow._daily_adv("AAA", _SEANS))

    assert beklenen is not None
    assert satir["qty"] == beklenen.qty
    assert satir["risk_dollars"] == pytest.approx(beklenen.risk_dollars)
    assert satir["sim_fill"] == pytest.approx(beklenen.entry)


def test_adv_penceresi_EOD_ile_BIREBIR_ayni(sandbox_state, saat):
    """`_adv` "d'den KESİNLİKLE ÖNCE"yi keser ve d'nin satırının frame'de olduğunu varsayar. Seans
    içinde bugünün günlük barı YOKTUR; `_adv`i olduğu gibi çağırmak DÜNÜ de düşürür ve pencere bir
    bar geriye kayardı — sessizce, EOD'den farklı bir likidite tavanıyla."""
    import pandas as pd
    from meridian.backtest import _adv
    _gunluk_barlar(sandbox_state, n=40)

    gölge = intraday_shadow._daily_adv("AAA", _SEANS)

    # EOD görünümü: bugünün (07-27) günlük barı YAZILMIŞ hâli.
    df = pd.read_csv(sandbox_state / "bars" / "aaa.csv", usecols=["date", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df.loc[pd.Timestamp(_SEANS), "volume"] = 12_345_678.0        # bugünün hacmi — pencereye GİRMEMELİ
    eod = _adv(df.sort_index(), pd.Timestamp(_SEANS))

    assert gölge == pytest.approx(eod), "gölge ADV penceresi EOD'ninkinden kaymış"


# =================================================================================================
# 2) SEANSTA PLAN BAŞINA TEK SATIR
# =================================================================================================
def test_ayni_plan_ayni_seansta_IKINCI_satir_yazmaz(sandbox_state, saat):
    """Tetik kesildikten sonra bar high'ı eşiğin üstünde kaldığı sürece HER olayda geçiş görünür.
    Her birine satır yazmak defteri aynı kararın kopyalarıyla şişirir ve 'kaç emir çıkardı'
    sayımını yalanlardı."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    plan = _plan()

    assert intraday_shadow.record(plan, _bar(), _SIMDI) is not None
    assert intraday_shadow.record(plan, _bar(dakika_once=1.0), _SIMDI) is None

    assert len(store.read_jsonl(intraday_shadow.ORDERS_FILE)) == 1


def test_dedup_SURECI_yeniden_baslasa_da_tutar(sandbox_state, saat):
    """Dedup yalnız RAM'de yaşarsa seans ortasındaki bir restart onu sıfırlar ve sayım sessizce
    şişer. Bellek boşaltılsa bile defterden yeniden yüklenmeli."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    intraday_shadow.record(_plan(), _bar(), _SIMDI)

    intraday_shadow.reset_dedup()                     # "süreç yeniden başladı"
    assert intraday_shadow.record(_plan(), _bar(), _SIMDI) is None
    assert len(store.read_jsonl(intraday_shadow.ORDERS_FILE)) == 1


# =================================================================================================
# 3) KAPILAR — her biri adıyla bloklar
# =================================================================================================
def test_halt_bloklar(sandbox_state, saat):
    _saglikli_state(sandbox_state, halted=True)
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(), _bar(), _SIMDI)

    assert satir["status"] == "blocked:halt"
    assert satir["gates"]["halt"] is True
    assert satir["qty"] is None and satir["sim_fill"] is None, "bloklanan kararda boyut UYDURULMAZ"


def test_pozisyon_zaten_varsa_bloklar(sandbox_state, saat):
    poz = {"plan_id": "P-ESKI", "ticker": "AAA", "side": "long", "entry": 100.0, "stop": 95.0,
           "trail_stop": 95.0, "target": 130.0, "qty": 10, "r_per_share": 5.0,
           "risk_dollars": 50.0, "size_r": 1.0, "ts_open": "2026-07-20"}
    _saglikli_state(sandbox_state, positions={"AAA": poz})
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(), _bar(), _SIMDI)

    assert satir["status"] == "blocked:position_exists"
    assert satir["gates"]["position_exists"] is True


def test_devre_kesici_bloklar(sandbox_state, saat):
    _saglikli_state(sandbox_state, day_pnl_pct=-0.99)      # limitin çok altında
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(), _bar(), _SIMDI)

    assert satir["status"] == "blocked:breaker" and satir["gates"]["breaker"] is True


def test_veri_kapisi_bloklar(sandbox_state, saat):
    _saglikli_state(sandbox_state, data_halt=True)
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(), _bar(), _SIMDI)

    assert satir["status"] == "blocked:data_bad" and satir["gates"]["data_bad"] is True


def test_derisk_sifirlanınca_bloklar(sandbox_state, saat):
    """Rampa TABANINDA ve ötesinde yeni boyut alınmaz (derisk_mult=0) — EOD'nin `size_mult > 0`
    kapısı. SENARYO DERİNLEŞTİRİLDİ (2026-08-12): taban %8 → %36 (goal.yaml
    `limits.derisk_floor_dd`, operatör kararı §E.1/§E.3), yani eski −15.000$ artık TAM BOY
    bölgesindedir ve testi sessizce etkisiz bırakırdı. Zarar tabanın ötesine taşındı."""
    _saglikli_state(sandbox_state, realized_pnl=-40_000.0, peak=100_000.0)
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(), _bar(), _SIMDI)

    assert satir["status"] == "blocked:size_mult" and satir["gates"]["size_mult"] == 0.0


def test_broker_kurali_bloklar_gap_through_stop(sandbox_state, saat):
    """`fill_entry` None döndüğünde (burada: bar stop'un ALTINDA açtı → geçerli giriş yok) gerekçe
    ADLANDIRILIR ama fill_entry mantığı DIŞARIDA yeniden hesaplanmaz — ikinci kopya sürüklenir."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    plan = _plan(stop=120.0, entry_trigger=105.0)     # sim_price = max(100, 105) = 105 <= stop
    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)

    assert satir["status"] == "blocked:broker_kurali"
    assert satir["qty"] is None
    assert _blocking_gate_hepsi_gecti(satir), "ön kapılar geçmeliydi; ret broker kuralından gelmeli"


def _blocking_gate_hepsi_gecti(satir: dict) -> bool:
    g = satir["gates"]
    return (not g["halt"] and not g["breaker"] and not g["data_bad"]
            and g["size_mult"] > 0 and not g["position_exists"] and g["max_open_ok"])


def test_olculemeyen_kapi_fail_CLOSED(sandbox_state, saat):
    """Kaynak dosya hiç yoksa kapı ÖLÇÜLEMEDİ demektir. 'Geçti' saymak fail-open olurdu; gölge
    ölçemediği kapıyı adıyla engeller."""
    store.write_json("portfolio.json", {"cash": 100_000.0, "realized_pnl": 0.0, "positions": {},
                                        "armed": [], "peak_equity": 100_000.0})
    _gunluk_barlar(sandbox_state)                      # heartbeat.json YOK → day_pnl_pct ölçülemez

    satir = intraday_shadow.record(_plan(), _bar(), _SIMDI)

    assert satir["status"] == "blocked:breaker_olculemedi"
    assert satir["gates"]["breaker"] is None


# =================================================================================================
# 4) SIFIR YETKİ — tek yazılan dosya gölge defteri
# =================================================================================================
def test_yalniz_kendi_defterine_yazar_baska_HICBIR_state_dosyasina_dokunmaz(sandbox_state, saat):
    """'Ölçüyorum' diyen bir katmanın sessizce durum değiştirmesi, bu deponun kovaladığı hata
    sınıfının en pahalısıdır. Dosya seti ve portfolio.json içeriği bayt bayt karşılaştırılır."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    once = {p.name: p.read_bytes() for p in sandbox_state.iterdir() if p.is_file()}

    intraday_shadow.record(_plan(), _bar(), _SIMDI)

    sonra = {p.name: p.read_bytes() for p in sandbox_state.iterdir() if p.is_file()}
    yeni = set(sonra) - set(once)
    # `events.jsonl` DURUM değil GÖZLEM defteridir — obs.log'un ortak kanalı, her modül oraya yazar
    # (intraday_cycle dâhil). Onu yasaklamak, gölgeyi sessiz bir katman yapmak olurdu (YASA 4).
    assert yeni <= {intraday_shadow.ORDERS_FILE, "events.jsonl"}, f"beklenmedik yeni dosya: {yeni}"
    assert intraday_shadow.ORDERS_FILE in yeni, "gölge defteri hiç yazılmadı"
    degisen = [k for k in once if once[k] != sonra[k]]
    assert degisen == [], f"gölge mevcut state dosyalarını DEĞİŞTİRDİ: {degisen}"
    assert not (sandbox_state / "INTRADAY_ARM").exists(), "gölge gerçek icra bayrağına dokundu"
    # Canlı defterin İÇERİĞİ de aynen durmalı (dosya seti aynı kalıp içerik değişseydi yukarıdaki
    # bayt karşılaştırması zaten yakalardı; bu satır niyeti okunur kılar).
    assert store.read_json("portfolio.json", {})["positions"] == {}


def test_statik_hicbir_emir_yolu_yok():
    """Kaynakta emir/kalıcılık yolu bulunmamalı — gelecekte biri 'küçük bir dokunuş' yaptığında
    bu test kırılsın diye statik."""
    src = SRC.read_text()
    # ÇAĞRI şekli aranır, kelime değil: gerekçe yorumlarında `_save_broker`tan BAHSETMEK (neden
    # çağrılmadığını anlatmak) meşrudur; onu ÇAĞIRMAK değildir. Kelime araması bu ikisini
    # ayırt edemez ve doğru yazılmış bir gerekçeyi cezalandırırdı.
    for yasak in ("_save_broker(", "submit_order", "close_all(", "store.write_json(",
                  "import alpaca", "adapters import alpaca", "adapters.alpaca"):
        assert yasak not in src, f"gölge modülünde yasak yol: {yasak}"
    assert "append_jsonl" in src, "defter yazımı store'un ortak yolundan geçmeli"
    # Kalıcılık yolu YALNIZ kendi defterine gitmeli.
    import re
    for m in re.findall(r"append_jsonl\(([^,]+)", src):
        assert m.strip() == "ORDERS_FILE", f"gölge başka bir deftere yazıyor: {m}"


def test_kanca_MERIDIAN_SHADOW_0_ile_no_op(sandbox_state, saat, monkeypatch):
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    monkeypatch.setattr(intraday_shadow, "ENABLED", False)

    assert intraday_shadow.record(_plan(), _bar(), _SIMDI) is None
    assert store.read_jsonl(intraday_shadow.ORDERS_FILE) == []


def test_kanca_intraday_cycle_icinde_KABLOLU():
    """YASA 6'nın diğer yüzü: fonksiyon var olmak yetmez, ÇAĞRILMASI gerekir. Kablolanmamış bir
    gölge katmanı sonsuza dek boş bir defter üretir ve pano 'henüz ölçmedi' der — sebebi görünmeden."""
    import inspect
    from meridian import intraday_cycle
    src = inspect.getsource(intraday_cycle.IntradayConsumer._handle_symbol)
    assert "intraday_shadow.record" in src, "tetik-geçişinde gölge çağrılmıyor"
    # SÖZLEŞME SIKILAŞTI (sadeleştirme turu, 2026-07-30): 4a gözlemi GÜNÜN TÜM PLANLARINA açıldı,
    # `intraday_shadow.record` ise BİLEREK yalnız SİLAHLI planda çağrılır. Gerekçe ölçümün
    # geçerliliğidir: silahlanmamış bir plan EOD'de hiç dolmaz, o yüzden onun satırı `vs_eod`ta
    # `n_unpaired`e düşer ve "gölge-vs-EOD friksiyon farkı" ölçümünü sulandırırdı.
    #
    # METİN TAZELENDİ (v219 devri, 2026-08-09) — ÖLÇÜLEN GERÇEK ARTIK İKİ KOLLU. Eski hâli "gölge
    # yalnız silahlı planda ÇALIŞIR" diyordu; v217'den (kart EXE-2026-003, 60181a1) beri bu cümle
    # KATMAN için yanlış, bu ASSERT için doğru. Ayrımı yapan şey defterdir:
    #   * SİLAHLI KOL — `if fired and is_armed_plan:` → `intraday_shadow.record` →
    #     `intraday_shadow_orders.jsonl`. Aşağıdaki çivi TAM OLARAK bunu tutar ve tutmaya devam
    #     eder; `vs_eod` ile `faz5_cikis` YALNIZ bu defteri okur.
    #   * PLANLI KOL — `elif fired and plan is not None:` → `intraday_shadow.planli_satir` →
    #     AYRI defter (`intraday_shadow_planli_orders.jsonl`). Yukarıdaki 2026-07-30 gerekçesi
    #     KALKMADI, ÇÖZÜLDÜ: ayrı defter olduğu için silahli kolun nüfusuna tek satır bile
    #     karışmıyor, yani sulandırma riski kaynağında yok.
    # Bu testin kapsamı DEĞİŞMEDİ ve genişletilmedi: silahli kolun kablosunu çivler. Planli kolun
    # kendi çivileri `tests/test_golge_planli_kol_v217.py`dedir (altın satır + ayrık defter +
    # kill#4 kirlenmezliği); bu dosyanın onlara İKİNCİ bir kopyasını yazması, iki çivinin zamanla
    # ayrışması demek olurdu.
    assert "if fired and is_armed_plan:" in src, \
        "gölge yalnız tetik KESİLDİĞİNDE ve SİLAHLI planda çağrılmalı"


def test_loop_py_gölgeye_hic_dokunmadi():
    """Bu turun kırmızı çizgisi: canlı EOD motoru sıfır temas."""
    loop_src = pathlib.Path("meridian/loop.py").read_text()
    assert "intraday_shadow" not in loop_src, "loop.py gölge katmanına bağlanmış"


# =================================================================================================
# 5) LOOK-AHEAD + SİM FİYAT SÖZLEŞMESİ
# =================================================================================================
def test_her_satirda_as_of_close_ts_ten_SONRA(sandbox_state, saat):
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(), _bar(), _SIMDI)

    a = dt.datetime.fromisoformat(satir["decision_as_of"])
    c = dt.datetime.fromisoformat(satir["close_ts"])
    assert a >= c, "karar anı barın KAPANIŞINDAN önce — look-ahead"
    assert satir["bar_t"] and satir["date"] == _SEANS


def test_gap_senaryosunda_sim_price_bar_acilisi(sandbox_state, saat):
    """Bar tetiğin ÜSTÜNDE açtıysa açılışı ödersin — bar içi sıralama bilinemez, sözleşme bilinçli
    olarak muhafazakârdır (asla tetikten ucuza dolmaz)."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(entry_trigger=105.0), _bar(o=107.5, h=112.0), _SIMDI)

    assert satir["sim_price"] == 107.5 and satir["bar_open"] == 107.5
    assert satir["sim_price_rule"] == "max(bar_open, entry_trigger)"


def test_tetigin_altinda_acilista_sim_price_tetik(sandbox_state, saat):
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)

    satir = intraday_shadow.record(_plan(entry_trigger=105.0), _bar(o=100.0), _SIMDI)

    assert satir["sim_price"] == 105.0


# =================================================================================================
# 6) vs_eod — gölge kararı ile GERÇEK dolgunun farkı
# =================================================================================================
def test_vs_eod_kapanmis_islemle_eslesir_ve_farki_dogru_hesaplar(sandbox_state, saat):
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    satir = intraday_shadow.record(_plan(), _bar(o=100.0), _SIMDI)
    sim_fill = satir["sim_fill"]
    eod_fill = sim_fill * 1.02                     # EOD ertesi açılışta %2 yukarıdan doldu
    store.write_jsonl("trades.jsonl", [{"plan_id": satir["plan_id"], "ticker": "AAA",
                                        "entry": eod_fill, "exit": 120.0}])

    out = intraday_shadow.vs_eod()

    assert out["n_paired"] == 1 and out["n_unpaired"] == 0
    assert out["recent"][0]["delta_pct"] == pytest.approx(2.0, abs=1e-3)
    assert out["mean_delta_pct"] == pytest.approx(2.0, abs=1e-3)


def test_vs_eod_acik_pozisyonla_da_eslesir(sandbox_state, saat):
    """Kıyas, işlem KAPANMADAN da yapılabilmeli — aksi hâlde kanıt aylarca beklerdi."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    satir = intraday_shadow.record(_plan(), _bar(o=100.0), _SIMDI)
    pf = store.read_json("portfolio.json", {})
    pf["positions"] = {"AAA": {"plan_id": satir["plan_id"], "ticker": "AAA", "side": "long",
                               "entry": satir["sim_fill"], "stop": 95.0, "trail_stop": 95.0,
                               "target": 130.0, "qty": 5, "r_per_share": 5.0,
                               "risk_dollars": 25.0, "size_r": 1.0, "ts_open": "2026-07-27"}}
    store.write_json("portfolio.json", pf)

    out = intraday_shadow.vs_eod()

    assert out["n_paired"] == 1
    assert out["recent"][0]["delta_pct"] == pytest.approx(0.0, abs=1e-6)


def test_vs_eod_eslesmeyen_satir_UNPAIRED_sayilir(sandbox_state, saat):
    """Eşleşmeyenin SEBEBİNE girilmez (kapı reddetti / plan hiç dolmadı / başka fiyat) — ölçülemeyen
    ölçülmemiş kalır; sayılır ama sınıflandırılmaz."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    intraday_shadow.record(_plan(), _bar(o=100.0), _SIMDI)

    out = intraday_shadow.vs_eod()

    assert out["n_paired"] == 0 and out["n_unpaired"] == 1
    assert out["mean_delta_pct"] is None, "çift yokken ortalama UYDURULMAZ"


def test_bloklanan_satir_kiyasa_GIRMEZ(sandbox_state, saat):
    _saglikli_state(sandbox_state, halted=True)
    _gunluk_barlar(sandbox_state)
    intraday_shadow.record(_plan(), _bar(), _SIMDI)

    out = intraday_shadow.vs_eod()
    assert out["n_paired"] == 0 and out["n_unpaired"] == 0


# =================================================================================================
# 7) YASA 6 — üretilen her alan bir yüzeyde okunuyor
# =================================================================================================
def test_yasa6_golge_alanlari_panoda_tuketiliyor(sandbox_state, saat):
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    satir = intraday_shadow.record(_plan(), _bar(o=100.0), _SIMDI)
    js = APP_JS.read_text()

    for k in ("ticker", "sim_price", "sim_fill", "qty", "risk_dollars", "entry_trigger",
              "status", "gates", "bar_t"):
        assert k in js, f"gölge satır alanı '{k}' panoda hiç okunmuyor"
    for k in satir["gates"]:
        assert k in js, f"gates.{k} panoda hiç okunmuyor"

    rapor = intraday_shadow.summarize(store.read_jsonl(intraday_shadow.ORDERS_FILE))
    for k in rapor:
        assert k in js, f"report.{k} panoda hiç okunmuyor"
    for k in rapor["vs_eod"]:
        assert k in js, f"vs_eod.{k} panoda hiç okunmuyor"


def test_api_diagnostics_golgeyi_servis_ediyor():
    """Defterin DIŞ okuyucusu api.py'dir (kendi yazdığını kendi okuyan tüketici sayılmaz)."""
    api_src = pathlib.Path("meridian/api.py").read_text()
    assert "intraday_shadow" in api_src and '_intra["shadow"]' in api_src
    # Defteri LİTERAL adıyla api.py okumalı: codelaw.artifact_graph yalnız böyle bir okumayı DIŞ
    # tüketici sayar (erişimci fonksiyon üzerinden dolaylı okuma statik grafta görünmez ve artefakt
    # "yazılıyor ama okunmuyor" ihlaline düşerdi).
    assert 'store.read_jsonl("intraday_shadow_orders.jsonl")' in api_src


def test_defter_satiri_json_serilesebilir(sandbox_state, saat):
    """Uç bu satırı telden geçirecek: numpy/NaN sızarsa /api/diagnostics tamamen 500 olur."""
    _saglikli_state(sandbox_state)
    _gunluk_barlar(sandbox_state)
    intraday_shadow.record(_plan(), _bar(o=100.0), _SIMDI)

    ham = (sandbox_state / intraday_shadow.ORDERS_FILE).read_text().strip()
    json.loads(ham)                                   # bozuksa burada patlar
    json.dumps(intraday_shadow.summarize(store.read_jsonl(intraday_shadow.ORDERS_FILE)),
               allow_nan=False)

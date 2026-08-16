"""test_golge_planli_kol_v217.py — 4B GÖLGENİN İKİNCİ KOLU (kart EXE-2026-003, 2026-08-09).

4b gölge katmanı bugüne dek yalnız SİLAHLANMIŞ planların dolumunu yazıyordu: 6 seansta 4 satır.
Tetiği kesilen ama silahlanmamış GO/REVIEW planları da ölçülürse, dakika-hassas icra sorusu SIFIR
ek pazar riskiyle çok daha geniş bir örneklemden sorulabilir. Bu dosya o genişletmenin dört sözünü
çiviler:

  (1) SİLAHLI KOL BAYT DÜZEYİNDE DEĞİŞMEDİ. Kartın kill#3'ü "şemasında/sayımında HERHANGİ bir
      fark → derhal geri alınır" diyor. Altın satır DEĞİŞİKLİKTEN ÖNCEKİ koddan alındı ve burada
      donduruldu; `kol` alanı silahli satıra EKLENMEDİ bile.
  (2) EXE-2026-002'NİN GERÇEK-ÇİFT HATTI KİRLENMİYOR. Bu bir üslup tercihi değil, ÖLÇÜLMÜŞ bir
      zorunluluk: `faz5_cikis` gölge defterini kol süzgeci OLMADAN okur ve evreni "sim_fill üretmiş
      her satır"dır. Silahlanmamış plan iç EOD defterinde hiç dolmaz — planli satırlar aynı deftere
      yazılsaydı hepsi `eod_yok` sınıfına düşer, eşleşmeme oranı %20 tavanını aşar ve KILL#4 Faz-5
      kilidini "ölçüldü"den "ölçülemedi"ye GERİ ALIRDI. Ayrı defter bu yüzden var.
  (3) DOLUM KURALI İKİ KOLDA BİREBİR AYNI. `sim_price = max(bar_open, entry_trigger)` tek gövdeden
      (`_satir`) çıkar; iki kopya kural, kol karşılaştırmasını anlamsız kılardı.
  (4) GÖZLEM İCRAYI YAVAŞLATMAZ (kill#1, p95 +%10 tavanı). Ölçüm düzeneği burada, sentetik yükle.

İKİNCİL HAT (gölge × cf) BURADA DA KİLİT AÇMAZ: ayrı rapor alanıdır, `health.faz6_kilitleri`ne
bağlanmadığı statik olarak da çivilenir.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import time

import pytest

from meridian import barclock as bc, config, faz5_cikis, intraday_cycle as ic, \
    intraday_shadow as ish, store

UTC = dt.timezone.utc
RTH = dt.datetime(2026, 7, 23, 14, 46, 30, tzinfo=UTC)      # 10:46:30 ET — RTH açık
SEANS = "2026-07-23"
PLAN_GUNU = "2026-07-22"                                     # planlar kapanışta kurulur
KART_YOLU = pathlib.Path("research/cards/EXE-2026-003-golge-planli-kol.yaml")
SHADOW_SRC = pathlib.Path("meridian/intraday_shadow.py")
CYCLE_SRC = pathlib.Path("meridian/intraday_cycle.py")

# ------------------------------------------------------------------------------------------------
# ALTIN SATIR — DEĞİŞİKLİKTEN **ÖNCEKİ** `intraday_shadow.record` çıktısı (2026-08-09, v217 öncesi
# kaynakla üretildi). `store.append_jsonl` satırı `json.dumps(payload)` ile yazar, yani aşağıdaki
# özet diskteki BAYTIN özetidir.
# TEK MEŞRU KIRILMA SEBEBİ: `state/goal.yaml`ın `slippage_bps`/`commission_per_share` alanları
# değişirse `sim_fill` değişir ve altın satır YENİDEN ALINMALIDIR. Başka her kırılma, kartın
# kill#3'ünün ateşlemesi demektir (silahli kolun şeması/sayımı değişti → geri al).
# ------------------------------------------------------------------------------------------------
ALTIN_SHA256 = "30c154cc96bf80c784702767dd04feeb5ab61dbe266c61d098ed97bedfe028d6"
ALTIN_ANAHTARLAR = ["plan_id", "ticker", "date", "entry_trigger", "bar_open", "sim_price",
                    "sim_price_rule", "sim_fill", "qty", "risk_dollars", "stop", "target",
                    "atr", "limit", "atr_kaynak", "pivot", "pivot_kaynak", "gap_at_submit",
                    "gap_at_submit_kaynak", "red_nedeni", "gates", "gate_inputs_as_of", "status",
                    "decision_as_of", "bar_t", "close_ts"]
ALTIN_SIMDI = dt.datetime(2026, 7, 27, 15, 40, 0, tzinfo=UTC)
ALTIN_SEANS = "2026-07-27"


@pytest.fixture(autouse=True)
def _temiz():
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()
    yield
    bc.reset_clock()
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()


# ---- ortak kurulum -----------------------------------------------------------------------------
def _kapilar_olculebilir(peak=100_000.0, positions=None, armed=None, last_date=PLAN_GUNU):
    """Gölge, KAYNAĞI OLMAYAN kapıyı fail-closed sayar: heartbeat/data_quality yoksa satır
    `blocked:breaker_olculemedi` olur ve hiç `sim_fill` üretmez — yani ölçtüğümüz şey kol değil,
    eksik fikstür olurdu."""
    store.write_json("portfolio.json", {"cash": 100_000.0, "realized_pnl": 0.0, "last_id": 0,
                                        "positions": positions or {}, "armed": armed or [],
                                        "peak_equity": peak, "day_start_equity": 100_000.0,
                                        "last_date": last_date})
    store.write_json("heartbeat.json", {"ts": f"{SEANS}T13:56:11+00:00", "day_pnl_pct": 0.0})
    store.write_json("data_quality.json", {"date": PLAN_GUNU, "data_halt": False})


def _plan(tk="AAA", trig=100.0, gun=PLAN_GUNU) -> dict:
    return {"id": f"P-{gun}-{tk}", "date": gun, "ticker": tk, "side": "long",
            "entry_trigger": trig, "stop": trig * 0.95, "profit_target": trig * 1.15,
            "size_r": 1.0, "setup": "breakout_vcp", "score": 80}


def _bar(t=f"{SEANS}T14:45:00Z", o=100.0, h=120.0, c=110.0) -> dict:
    return {"t": t, "o": o, "h": h, "l": o - 1.0, "c": c, "v": 5000.0}


def _bars_inject(monkeypatch, bars=None):
    monkeypatch.setattr(ic.hotstate, "read_bars", lambda tk, n: bars or [_bar()])


# =================================================================================================
# 1) PLANLI KOL YAZIYOR — ve etiketini TAŞIYOR
# =================================================================================================
def test_planli_kol_YAZIYOR_ve_kol_etiketini_tasiyor(sandbox_state, monkeypatch):
    """Turun asıl kazancı: silahlı plan YOK, açık pozisyon YOK. Eski davranışta gölge defteri bu
    seansta SIFIR satır görürdü (canlıdaki hâl: 10 plan / 0 silahlı)."""
    bc.set_clock(lambda: RTH)
    _kapilar_olculebilir()
    store.append_jsonl("trade_plans.jsonl", _plan())
    _bars_inject(monkeypatch)

    ic.consumer().on_barfeed_event({"syms": "AAA"})

    planli = store.read_jsonl(ish.PLANLI_ORDERS_FILE)
    assert len(planli) == 1, "planli kol yazmadı — kablolama çalışmıyor"
    r = planli[0]
    assert r["kol"] == ish.KOL_PLANLI, "kol etiketi ZORUNLU (kart: universe)"
    assert r["status"] == "would_submit" and r["sim_fill"] is not None
    assert r["plan_id"] == f"P-{PLAN_GUNU}-AAA" and r["date"] == SEANS
    assert r["sim_price_rule"] == "max(bar_open, entry_trigger)"
    # SIFIR YETKİ, planli kolda da: plan silahlanmadı, pozisyon açılmadı.
    pf = store.read_json("portfolio.json", {})
    assert pf["armed"] == [] and pf["positions"] == {}
    assert not (sandbox_state / "INTRADAY_ARM").exists()
    # Sayaç AYRI: silahli kolun sayısı (pano `shadow_written`) DEĞİŞMEDİ.
    h = ic.health()
    assert h["shadow_planli_written"] == 1 and h["shadow_written"] == 0


def test_planli_yazim_SILAHLI_DEFTERE_dokunmaz(sandbox_state, monkeypatch):
    """Kartın kill#3'ü sayıma da bakar: planli kol yazarken silahli defterin BAYTI değişmemeli."""
    bc.set_clock(lambda: RTH)
    _kapilar_olculebilir()
    store.append_jsonl("trade_plans.jsonl", _plan())
    _bars_inject(monkeypatch)
    silahli_yol = sandbox_state / ish.ORDERS_FILE
    silahli_yol.write_text('{"plan_id": "P-2026-07-01-ZZZ", "date": "2026-07-01"}\n')
    once = silahli_yol.read_bytes()

    ic.consumer().on_barfeed_event({"syms": "AAA"})

    assert silahli_yol.read_bytes() == once, "planli kol silahli deftere yazdı"
    assert len(store.read_jsonl(ish.PLANLI_ORDERS_FILE)) == 1


def test_silahli_plan_ESKI_YOLDAN_gider_planli_defter_bos_kalir(sandbox_state, monkeypatch):
    """İki kol AYRI: silahlı plan eski defterine, planli defter boş kalır (nüfus karışmaz)."""
    bc.set_clock(lambda: RTH)
    p = _plan("MSFT", 50.0)
    _kapilar_olculebilir(armed=[p])
    _bars_inject(monkeypatch, [_bar(o=50.0, h=60.0, c=55.0)])

    ic.consumer().on_barfeed_event({"syms": "MSFT"})

    assert len(store.read_jsonl(ish.ORDERS_FILE)) == 1
    assert store.read_jsonl(ish.PLANLI_ORDERS_FILE) == []
    h = ic.health()
    assert h["shadow_written"] == 1 and h["shadow_planli_written"] == 0


def test_planli_kol_SEANSTA_TEK_satir_ve_restart_sonrasi_da(sandbox_state, monkeypatch):
    """Tetik kesildikten sonra bar high'ı eşiğin üstünde kaldığı sürece HER olayda geçiş görünür.
    Dedup yalnız RAM'de yaşasaydı seans ortasındaki bir restart kartın BİRİNCİL ölçütünü
    ("20 seansta ≥ 40 dolum") kendi kopyalarıyla doldururdu."""
    bc.set_clock(lambda: RTH)
    _kapilar_olculebilir()
    store.append_jsonl("trade_plans.jsonl", _plan())
    _bars_inject(monkeypatch)

    ic.consumer().on_barfeed_event({"syms": "AAA"})
    ic.consumer().on_barfeed_event({"syms": "AAA"})
    assert len(store.read_jsonl(ish.PLANLI_ORDERS_FILE)) == 1

    ish.reset_dedup()                                    # "süreç yeniden başladı"
    ic.consumer().on_barfeed_event({"syms": "AAA"})
    assert len(store.read_jsonl(ish.PLANLI_ORDERS_FILE)) == 1, \
        "restart sonrası ikinci satır — dedup defterden yüklenmiyor"


def test_kol_KAPATMA_anahtari_yalniz_yeni_kolu_susturur(sandbox_state, monkeypatch):
    """kill#1/kill#2 "kol kapatılır / yazım durur" diyor — kapatma yolu OLMALI, ve silahli kolun
    kanıt zincirini (EXE-2026-002) yanında götürmemeli."""
    bc.set_clock(lambda: RTH)
    p = _plan("MSFT", 50.0)
    _kapilar_olculebilir(armed=[p])
    store.append_jsonl("trade_plans.jsonl", _plan("AAA", 100.0))
    _bars_inject(monkeypatch, [_bar(o=50.0, h=200.0, c=150.0)])
    monkeypatch.setattr(ish, "PLANLI_ENABLED", False)

    ic.consumer().on_barfeed_event({"syms": "AAA,MSFT"})

    assert store.read_jsonl(ish.PLANLI_ORDERS_FILE) == [], "kol kapalıyken yazdı"
    assert len(store.read_jsonl(ish.ORDERS_FILE)) == 1, "kapatma anahtarı silahli kolu da susturdu"


# =================================================================================================
# 2) SİLAHLI KOL BAYT DÜZEYİNDE DEĞİŞMEDİ (kart kill#3)
# =================================================================================================
def _altin_satiri_uret() -> dict:
    plan = {"id": "P-2026-07-27-AAA", "ticker": "AAA", "side": "long", "entry_trigger": 105.0,
            "stop": 95.0, "profit_target": 130.0, "size_r": 1.0, "r_multiple_expected": 2.5,
            "regime_at_plan": "chop", "strategy_version": 4, "setup": "breakout_vcp", "score": 80}
    t = ALTIN_SIMDI - dt.timedelta(minutes=2)
    bar = {"t": t.strftime("%Y-%m-%dT%H:%M:00Z"), "o": 100.0, "h": 112.0, "l": 99.0, "c": 110.0,
           "v": 5000.0}
    return ish.record(plan, bar, ALTIN_SIMDI)


def _altin_fikstur(state):
    import pandas as pd
    store.write_json("portfolio.json", {"cash": 100_000.0, "realized_pnl": 0.0, "last_id": 0,
                                        "positions": {}, "armed": [], "peak_equity": 100_000.0,
                                        "day_start_equity": 100_000.0})
    store.write_json("heartbeat.json", {"ts": "2026-07-27T13:56:11+00:00", "day_pnl_pct": 0.0})
    store.write_json("data_quality.json", {"date": "2026-07-24", "data_halt": False})
    dates = pd.bdate_range(end="2026-07-24", periods=40).strftime("%Y-%m-%d").tolist()
    satir = ["date,open,high,low,close,volume"]
    for i, d in enumerate(dates):
        satir.append(f"{d},100,101,99,100,{800_000.0 + i}")
    (state / "bars" / "aaa.csv").write_text("\n".join(satir) + "\n")


def test_silahli_kolun_satiri_BAYT_BAYT_ayni(sandbox_state, monkeypatch):
    """ÖNCE/SONRA KANITI. Özet, v217 DEĞİŞİKLİĞİNDEN ÖNCEKİ kaynakla üretilmiş satırın özetidir."""
    monkeypatch.setattr(bc, "now", lambda: ALTIN_SIMDI)
    _altin_fikstur(sandbox_state)

    satir = _altin_satiri_uret()

    assert list(satir) == ALTIN_ANAHTARLAR, "silahli kolun ŞEMASI değişti (kart kill#3 → geri al)"
    assert "kol" not in satir, \
        "silahli satıra `kol` alanı eklenmiş — şema farkı, kartın derhal geri alma sebebi"
    bayt = json.dumps(satir)                        # store.append_jsonl'in yazdığı biçimin AYNISI
    assert hashlib.sha256(bayt.encode()).hexdigest() == ALTIN_SHA256, (
        "silahli kolun BAYTI değişti. Tek meşru sebep goal.yaml'ın slipaj/komisyon alanlarıdır "
        "(o zaman altın satır yeniden alınır); başka her sebep kill#3'tür.")
    # Diske inen satır da aynı olmalı (üretilen sözlük ≠ yazılan bayt olabilirdi).
    ham = (sandbox_state / ish.ORDERS_FILE).read_text().strip()
    assert hashlib.sha256(ham.encode()).hexdigest() == ALTIN_SHA256


def test_iki_kol_AYNI_dolum_kuralini_uygular(sandbox_state, monkeypatch):
    """Kart: `sim_price_rule` iki kolda BİREBİR aynı. İki gövde yazılsaydı kol karşılaştırması
    nüfus farkını değil iki kod yolunun farkını ölçerdi."""
    monkeypatch.setattr(bc, "now", lambda: ALTIN_SIMDI)
    _altin_fikstur(sandbox_state)
    plan = {"id": "P-2026-07-27-AAA", "ticker": "AAA", "side": "long", "entry_trigger": 105.0,
            "stop": 95.0, "profit_target": 130.0, "size_r": 1.0, "setup": "breakout_vcp"}
    bar = {"t": "2026-07-27T15:38:00Z", "o": 100.0, "h": 112.0, "l": 99.0, "c": 110.0, "v": 5000.0}

    silahli = ish.record(plan, bar, ALTIN_SIMDI)
    planli = ish.planli_satir(plan, bar, ALTIN_SIMDI)

    assert planli is not None
    assert set(planli) - set(silahli) == {"kol"}, "kollar YALNIZ etiketle ayrılmalı"
    for alan in ("sim_price", "sim_price_rule", "sim_fill", "qty", "risk_dollars", "status",
                 "gates", "entry_trigger", "bar_open"):
        assert planli[alan] == silahli[alan], f"kollar `{alan}` alanında ayrışıyor"


# =================================================================================================
# 3) EXE-2026-002'NİN GERÇEK-ÇİFT HATTI KİRLENMİYOR
# =================================================================================================
def _f5_fikstur():
    """Faz-5 hattının okuduğu üç kaynak: gölge defteri + kapanmış işlemler + portföy."""
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    for i, tk in enumerate(("AAA", "BBB")):
        pid = f"P-2026-07-2{i}-{tk}"
        store.append_jsonl(ish.ORDERS_FILE, {
            "plan_id": pid, "ticker": tk, "date": f"2026-07-2{i + 3}", "status": "would_submit",
            "sim_fill": 100.0, "qty": 10, "risk_dollars": 500.0,
            "decision_as_of": "x", "bar_t": "x", "close_ts": "x", "gate_inputs_as_of": {}})
        store.append_jsonl("trades.jsonl", {"plan_id": pid, "entry": 101.0, "side": "long"})


def test_EXE_2026_002_hatti_planli_defterden_ETKILENMIYOR(sandbox_state):
    """ÖLÇÜLMÜŞ ZORUNLULUK: planli satırlar aynı deftere yazılsaydı hepsi `eod_yok` sınıfına düşer,
    kill#4'ün %20 tavanı aşılır ve kilit "ölçüldü"den "ölçülemedi"ye GERİLERDİ. Aynı satırlar ayrı
    defterdeyken Faz-5 hükmü BİT BİT aynı kalmalı."""
    _f5_fikstur()
    once = faz5_cikis.cikis_olcumu()

    for i in range(8):                                   # kirletmeye YETECEK kadar planli satır
        store.append_jsonl(ish.PLANLI_ORDERS_FILE, {
            "plan_id": f"P-2026-07-22-P{i}", "ticker": f"P{i}", "date": SEANS,
            "status": "would_submit", "sim_fill": 100.0 + i, "qty": 10, "risk_dollars": 500.0,
            "kol": ish.KOL_PLANLI, "decision_as_of": "x", "bar_t": "x", "close_ts": "x",
            "gate_inputs_as_of": {}})
    sonra = faz5_cikis.cikis_olcumu()

    assert json.dumps(once, sort_keys=True, default=str) == \
        json.dumps(sonra, sort_keys=True, default=str), \
        "Faz-5 hükmü planli defterden etkilendi — EXE-2026-002 zinciri kirlendi"
    assert once["olcum"]["n_defter"] == 2 and once["olcum"]["eslesmeyen"]["n"] == 0


def test_faz5_hatti_YALNIZ_silahli_defteri_okuyor_STATIK():
    """Çalışma-anı kanıtının statik ikizi: kilit kodu planli defterin adını HİÇ görmemeli.
    (Bir gün biri "iki defteri birleştirip okuyalım" derse burada patlar.)"""
    f5 = pathlib.Path("meridian/faz5_cikis.py").read_text()
    assert ish.PLANLI_ORDERS_FILE not in f5 and "PLANLI_ORDERS_FILE" not in f5
    assert "from .intraday_shadow import ORDERS_FILE" in f5
    for yol in ("meridian/health.py", "meridian/api.py"):
        src = pathlib.Path(yol).read_text()
        assert ish.PLANLI_ORDERS_FILE not in src, \
            f"{yol} planli defteri okuyor — ikincil hat kilit zincirine sızmış"
        assert "golge_cf_eslestirme" not in src, \
            f"{yol} ikincil hattı çağırıyor — kart: bu hat kilidi AÇMAZ"


def test_planli_yazim_intraday_cycle_ICINDE_KABLOLU():
    """YASA 6'nın diğer yüzü: fonksiyon var olmak yetmez, ÇAĞRILMASI gerekir. Ayrıca yazımın
    NEREDE olduğu bir karardır (gölge modülünün tek lağımı `ORDERS_FILE`dır — v105 çivisi)."""
    src = CYCLE_SRC.read_text()
    assert "intraday_shadow.planli_satir(" in src, "planli kol hiç çağrılmıyor"
    assert "store.append_jsonl(intraday_shadow.PLANLI_ORDERS_FILE" in src, \
        "planli defter yazımı kablolanmamış (ya da başka bir yola kaymış)"
    assert "intraday_shadow.planli_yazildi(" in src, "tekilleştirme işareti basılmıyor"
    assert "if fired and is_armed_plan:" in src, "silahli kolun kancası değişmiş"
    # Gölge modülünün TEK lağımı hâlâ tek: planli yazım oraya geri sızmamalı.
    import re
    for m in re.findall(r"append_jsonl\(([^,]+)", SHADOW_SRC.read_text()):
        assert m.strip() == "ORDERS_FILE", f"gölge modülü ikinci bir deftere yazıyor: {m}"


# =================================================================================================
# 4) KOL ETİKETİ ZORUNLU (okuma yüzeyi)
# =================================================================================================
def test_kol_etiketi_HER_SATIRDA_zorunlu_ve_etiketsiz_satir_evrene_girmez(sandbox_state):
    """Silahli kolun DİSKTEKİ satırına `kol` yazılmadı (kill#3); etiket okuma anında basılır.
    Planli defterde etiketsiz bir satır bulunursa UYDURULMAZ — adıyla dışarıda kalır."""
    store.append_jsonl(ish.ORDERS_FILE, {"plan_id": "P-2026-07-22-AAA", "date": SEANS,
                                         "sim_fill": 100.0})
    store.append_jsonl(ish.PLANLI_ORDERS_FILE, {"plan_id": "P-2026-07-22-BBB", "date": SEANS,
                                                "sim_fill": 101.0, "kol": ish.KOL_PLANLI})
    store.append_jsonl(ish.PLANLI_ORDERS_FILE, {"plan_id": "P-2026-07-22-CCC", "date": SEANS,
                                                "sim_fill": 102.0})          # ETİKETSİZ

    k = ish.kollar()

    assert all(r.get("kol") in (ish.KOL_SILAHLI, ish.KOL_PLANLI) for r in k["satirlar"])
    assert [r["kol"] for r in k["satirlar"]] == [ish.KOL_SILAHLI, ish.KOL_PLANLI]
    assert k["etiketsiz_n"] == 1 and "P-2026-07-22-CCC" in k["etiketsiz"][0]
    assert k["n"] == {ish.KOL_SILAHLI: 1, ish.KOL_PLANLI: 1}


def test_planli_kol_uretimi_PENCERE_DOLMADAN_hukum_vermez(sandbox_state):
    """Kartın birincil ölçütü de kill#2 de 20 SEANSA bakar. 12 seansta 8 dolum görüp "kill#2
    ateşledi" demek, dolmamış bir pencereden hüküm çıkarmak olurdu."""
    for i in range(3):
        store.append_jsonl(ish.PLANLI_ORDERS_FILE, {"plan_id": f"P-2026-07-0{i}-A", "date":
                                                    f"2026-07-0{i + 1}", "status": "would_submit",
                                                    "kol": ish.KOL_PLANLI})
    rapor = ish.planli_kol_uretimi()
    assert rapor["durum"] == "olculemedi" and rapor["pencere_tam_mi"] is False
    assert rapor["dolum_n"] == 3 and "PENCERE DOLMADI" in rapor["hukum"]
    assert rapor["hedef"] == 40 and rapor["kill_esigi"] == 10 and rapor["pencere_seans"] == 20


def test_bloklanan_satir_DOLUM_sayilmaz(sandbox_state):
    """`blocked:*` bir dolum DEĞİLDİR; onu saymak kolun verimini şişirir ve kill#2'yi susturur."""
    for i in range(25):
        store.append_jsonl(ish.PLANLI_ORDERS_FILE,
                           {"plan_id": f"P-2026-06-{i:02d}-A", "date": f"2026-06-{i + 1:02d}",
                            "status": "blocked:max_open", "kol": ish.KOL_PLANLI})
    rapor = ish.planli_kol_uretimi()
    assert rapor["pencere_tam_mi"] is True and rapor["dolum_n"] == 0
    assert "KILL#2" in rapor["hukum"]


# =================================================================================================
# 5) İKİNCİL HAT — GÖLGE × CF EŞLEŞTİRMESİ
# =================================================================================================
def _cf(id_, gun, tk, entry, **kw) -> dict:
    r = {"id": id_, "date": gun, "ticker": tk, "setup": "breakout_vcp", "status": "closed_target",
         "regime": "trend", "verdict": "GO", "entry": entry}
    r.update(kw)
    return r


def test_golge_cf_eslestirmesi_KART_FORMULUNU_uygular(sandbox_state):
    """Sentetik: iki kol, iki seans, dört çift. `kazanc_bps = (cf_giris − sim_fill)/cf_giris×10⁴`.

    İKİ SEANS ŞART: tek tarih kümesinde kümeler-arası dağılım kurulamaz ve `tarih_kumeli_bootstrap`
    aralığı DÜRÜSTÇE None döner (bu da ayrıca sınanır)."""
    golge, cfs = [], []
    for i, (gun, seans) in enumerate((("2026-07-20", "2026-07-21"), ("2026-07-21", "2026-07-22"))):
        for kol, tk in ((ish.KOL_SILAHLI, f"S{i}"), (ish.KOL_PLANLI, f"P{i}")):
            golge.append({"plan_id": f"P-{gun}-{tk}", "ticker": tk, "date": seans,
                          "sim_fill": 100.0, "kol": kol, "status": "would_submit"})
            cfs.append(_cf(f"CF-{gun}-{tk}-breakout_vcp", gun, tk, 101.0))

    rapor = ish.golge_cf_eslestirme(satirlar=golge, cf_rows=cfs)

    assert rapor["durum"] == "olculdu" and rapor["kilidi_acmaz"] is True
    assert rapor["eslesmeyen"]["n"] == 0
    beklenen = round((101.0 - 100.0) / 101.0 * 10000.0, 4)
    assert rapor["toplam"]["n"] == 4
    assert rapor["toplam"]["ort_bps"] == pytest.approx(beklenen, abs=1e-4)
    for kol in (ish.KOL_SILAHLI, ish.KOL_PLANLI):
        assert rapor["kollar"][kol]["n"] == 2
        assert rapor["kollar"][kol]["ort_bps"] == pytest.approx(beklenen, abs=1e-4)
    # Aralık tarih-kümeli gövdeden gelir (ikinci bir bootstrap yazılmadı) ve 2 küme görür.
    assert rapor["toplam"]["ci"]["n_kume"] == 2 and rapor["toplam"]["ci"]["B"] == 10_000
    assert rapor["toplam"]["n_min_dolu_mu"] is False and rapor["n_min"] == 40


def test_eslesmeme_SINIFLARI_ayri_ayri_adlandirilir(sandbox_state):
    """Tek "eşleşmedi" kovası, kök-neden turunu kör eder: `cf_yok` (anahtarın karşılığı yok),
    `cf_dolum_yok` (no_fill sınıfı), `plan_id_cozulemedi` (kimlik biçimi) AYRI sınıflardır."""
    golge = [
        {"plan_id": "P-2026-07-20-AAA", "ticker": "AAA", "date": "2026-07-21", "sim_fill": 100.0,
         "kol": ish.KOL_PLANLI},                                    # cf_yok
        {"plan_id": "P-2026-07-20-BBB", "ticker": "BBB", "date": "2026-07-21", "sim_fill": 100.0,
         "kol": ish.KOL_PLANLI},                                    # cf_dolum_yok (no_fill)
        {"plan_id": "GARIP-KIMLIK", "ticker": "CCC", "date": "2026-07-21", "sim_fill": 100.0,
         "kol": ish.KOL_PLANLI},                                    # plan_id_cozulemedi
    ]
    cfs = [_cf("CF-2026-07-20-BBB-breakout_vcp", "2026-07-20", "BBB", None,
               status="no_fill_gap")]

    rapor = ish.golge_cf_eslestirme(satirlar=golge, cf_rows=cfs)

    dag = rapor["eslesmeyen"]["sinif_dagilimi"]
    assert dag == {"cf_dolum_yok": 1, "cf_yok": 1, "plan_id_cozulemedi": 1}
    assert rapor["eslesmeyen"]["oran"] == 1.0
    assert all(n["neden"] for n in rapor["eslesmeyen"]["nedenler"])


def test_belirsiz_cf_eslesmesi_OLCULEMEDI_der(sandbox_state):
    """Aynı (gün, ticker) altında iki dolmuş plan satırı varsa "ilkini al" demek, hangi kurulumun
    fiyatıyla kıyasladığını bilmeden bir sayı yazmaktır."""
    golge = [{"plan_id": "P-2026-07-20-AAA", "ticker": "AAA", "date": "2026-07-21",
              "sim_fill": 100.0, "kol": ish.KOL_PLANLI}]
    cfs = [_cf("CF-2026-07-20-AAA-breakout_vcp", "2026-07-20", "AAA", 101.0),
           _cf("CF-2026-07-20-AAA-momentum_burst", "2026-07-20", "AAA", 103.0)]

    rapor = ish.golge_cf_eslestirme(satirlar=golge, cf_rows=cfs)

    assert rapor["eslesmeyen"]["sinif_dagilimi"] == {"cf_dolum_yok": 1}
    assert "BELİRSİZ" in rapor["eslesmeyen"]["nedenler"][0]["neden"]


def test_entry_trigger_IKINCI_ELEK_olarak_ayirir(sandbox_state):
    """Aynı gün aynı ticker iki kurulumdan plan üretebilir. Eşik fiyatı İKİ TARAFTA DA yazılı ve
    İKİ KOLDA DA aynı alandır — ayrım için şema değişikliği (silahli kola `setup` eklemek) gerekmez."""
    golge = [{"plan_id": "P-2026-07-20-AAA", "ticker": "AAA", "date": "2026-07-21",
              "sim_fill": 100.0, "entry_trigger": 99.0, "kol": ish.KOL_PLANLI}]
    cfs = [_cf("CF-2026-07-20-AAA-breakout_vcp", "2026-07-20", "AAA", 101.0, entry_trigger=99.0),
           _cf("CF-2026-07-20-AAA-momentum_burst", "2026-07-20", "AAA", 105.0, entry_trigger=90.0)]

    rapor = ish.golge_cf_eslestirme(satirlar=golge, cf_rows=cfs)

    assert rapor["toplam"]["n"] == 1
    assert rapor["toplam"]["ciftler"][0]["cf_giris"] == 101.0
    assert rapor["toplam"]["ciftler"][0]["cf_aday_n"] == 2


def test_OLCUM_OZDES_belirsizlik_olculebilir_ama_ADLANDIRILIR(sandbox_state):
    """Canlı korpusta ölçüldü (2026-08-09): çok-adaylı 157 anahtarın 157'sinde iki satır AYNI
    sinyalin iki kurulum adı altındaki kopyasıdır ve `entry` BİREBİR aynıdır. Hangi satırın
    seçildiği `kazanc_bps`i değiştirmez — ölçümü "belirsiz" diye ATMAK, ölçülebilir 314 satırı
    ölçülemez ilan etmek olurdu. Ama belirsizlik gizlenmez: `cf_aday_n` çiftin üstünde durur."""
    golge = [{"plan_id": "P-2026-07-20-AAA", "ticker": "AAA", "date": "2026-07-21",
              "sim_fill": 100.0, "entry_trigger": 99.0, "kol": ish.KOL_PLANLI}]
    cfs = [_cf("CF-2026-07-20-AAA-breakout_vcp", "2026-07-20", "AAA", 101.0, entry_trigger=99.0),
           _cf("CF-2026-07-20-AAA-momentum_burst", "2026-07-20", "AAA", 101.0, entry_trigger=99.0)]

    rapor = ish.golge_cf_eslestirme(satirlar=golge, cf_rows=cfs)

    assert rapor["toplam"]["n"] == 1 and rapor["eslesmeyen"]["n"] == 0
    c = rapor["toplam"]["ciftler"][0]
    assert c["cf_giris"] == 101.0 and c["cf_aday_n"] == 2


def test_uyuyan_ve_esik_alti_cf_satirlari_PLAN_SATIRININ_yerine_gecmez(sandbox_state):
    """Gölge satırı GERÇEK plandan doğdu; karşılığı da gerçek plan satırıdır. `DORMANT`/`NEAR_MISS`
    kayıtları aynı anahtarı paylaşır ama başka bir soruyu cevaplar."""
    golge = [{"plan_id": "P-2026-07-20-AAA", "ticker": "AAA", "date": "2026-07-21",
              "sim_fill": 100.0, "kol": ish.KOL_PLANLI}]
    cfs = [_cf("CF-2026-07-20-AAA-mb", "2026-07-20", "AAA", 90.0, verdict="NEAR_MISS",
               near_miss=True),
           _cf("CF-2026-07-20-AAA-breakout_vcp", "2026-07-20", "AAA", 101.0)]

    rapor = ish.golge_cf_eslestirme(satirlar=golge, cf_rows=cfs)

    assert rapor["toplam"]["n"] == 1
    assert rapor["toplam"]["ciftler"][0]["cf_giris"] == 101.0


def test_cf_DEFTERI_YOKKEN_olculemedi_der_SIFIR_yazmaz(sandbox_state):
    """UYDURMA YASAĞI: karşı bacak yoksa "0 bps" yazmak "iki sim aynı" iddiasıdır."""
    golge = [{"plan_id": "P-2026-07-20-AAA", "ticker": "AAA", "date": "2026-07-21",
              "sim_fill": 100.0, "kol": ish.KOL_PLANLI}]

    rapor = ish.golge_cf_eslestirme(satirlar=golge, cf_rows=[])

    assert rapor["durum"] == "olculemedi"
    assert rapor["toplam"] is None and rapor["kollar"] is None
    assert "cf defteri" in rapor["neden"] and rapor["kilidi_acmaz"] is True

    bos = ish.golge_cf_eslestirme(satirlar=[], cf_rows=[_cf("CF-x", "2026-07-20", "AAA", 101.0)])
    assert bos["durum"] == "olculemedi" and "DOLUM ÜRETMİŞ satır YOK" in bos["neden"]


def test_ikincil_hat_bootstrap_govdesini_FAZ5ten_alir():
    """Kart: "emsal faz5_cikis.tarih_kumeli_bootstrap — İMKANSA yeniden kullan, kopyalama".
    İkinci bir gövde yazılsaydı iki hattın aralığı zamanla ayrışır ve "iki hat uyuşuyor mu"
    sorusu ölçüm farkını gerçek fark sanardı."""
    src = SHADOW_SRC.read_text()
    assert "from .faz5_cikis import BOOTSTRAP_N, tarih_kumeli_bootstrap" in src
    assert "def tarih_kumeli_bootstrap" not in src, "bootstrap gövdesi KOPYALANMIŞ"
    assert "np.percentile" not in src and "default_rng" not in src


# =================================================================================================
# 6) KILL#1 — GÖZLEM İCRAYI YAVAŞLATAMAZ (p95 +%10 tavanı)
# =================================================================================================
P95_TAVAN = 1.10          # kart kill#1 — ölçümden ÖNCE donduruldu
_OLAY_N = 150             # bir seansın kadansını temsil eden olay dizisi (canlıda ~390)
_SEMBOL_N = 5
_TUR = 4                  # A/B/B/A serpiştirme: makine gürültüsü iki kola da aynı düşsün.
                          # HÜKÜM HAVUZLANMIŞ p95'ten okunur: 60 örneklik bir kuyruğun p95'i
                          # ±%25 oynuyordu (ölçüldü) — yani tavanı geçen/geçmeyen sonucu makinenin
                          # o anki gürültüsü belirlerdi, kolun maliyeti değil.


def _p95(vals: list[float]) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]


def _dongu_olc(monkeypatch, sandbox_state, *, planli_acik: bool) -> list[float]:
    """Bir seansın olay dizisini koştur, OLAY BAŞINA süreyi döndür.

    "Döngü" = bir barfeed olayının tamamı (`on_barfeed_event`), yani izlenen TÜM sembollerin
    işlenmesi — canlıdaki sıcak yol budur, tek sembol değil."""
    for ad in (ic.DECISIONS_FILE, ish.ORDERS_FILE, ish.PLANLI_ORDERS_FILE, "trade_plans.jsonl"):
        p = sandbox_state / ad
        if p.exists():
            p.unlink()
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()
    bc.set_clock(lambda: RTH)
    _bars_inject(monkeypatch)
    _kapilar_olculebilir()
    for i in range(_SEMBOL_N):
        store.append_jsonl("trade_plans.jsonl", _plan(f"T{i}", 100.0))
    monkeypatch.setattr(ish, "PLANLI_ENABLED", planli_acik)
    syms = ",".join(f"T{i}" for i in range(_SEMBOL_N))
    tuketici = ic.consumer()
    # ISINMA yalnız import/önbellek/dosya oluşturma içindir. Sonrasında tekilleştirme SIFIRLANIR ve
    # planli defter silinir: yeni kolun GERÇEK maliyeti (5 planın ilk yazımı) ÖLÇÜM PENCERESİNİN
    # İÇİNE düşsün. Isınmanın o maliyeti yutmasına izin vermek, ölçüm düzeneğini kendi lehine
    # kurmak olurdu — kartın tavanı o zaman hiçbir şeyi sınamazdı.
    tuketici.on_barfeed_event({"syms": syms})
    ish.reset_dedup()
    (sandbox_state / ish.PLANLI_ORDERS_FILE).unlink(missing_ok=True)
    sureler = []
    for _ in range(_OLAY_N):
        t0 = time.perf_counter()
        tuketici.on_barfeed_event({"syms": syms})
        sureler.append((time.perf_counter() - t0) * 1000.0)
    return sureler


def test_p95_dongu_suresi_kart_tavanini_ASMIYOR(sandbox_state, monkeypatch):
    """KILL#1: "gözlem, icrayı yavaşlatamaz — p95 döngü süresi +%10'dan fazla artarsa kol kapatılır".

    ÖLÇÜM DÜZENEĞİ BEYANLIDIR (rigging'in panzehiri): yük, canlının kadansını taklit eder — sabit
    bir plan nüfusu (5) ve o nüfusun tetiği KESİLDİĞİ bir seans dizisi (60 olay). Planli kolun
    maliyeti plan başına SEANSTA BİR kez ödenir (tekilleştirme), yani ilk olaya düşer; p95 o
    kuyruğu görmez. BU BİR KAÇAMAK DEĞİL, ÖLÇÜLEN ŞEYİN KENDİSİDİR: canlı sıcak yol seansta ~390
    olay işler ve plan nüfusu ~10'dur. En kötü olay (ilk yazımın düştüğü olay) ayrıca ölçülür ve
    rapora yazılır — kartın tavanı p95'e bakar, ama sayı gizlenmez.

    Taban kol `PLANLI_ENABLED=False`tur: "değişiklikten önceki kod"a en yakın hâl (fark, kapalı
    bir bayrağın okunmasıdır).
    """
    havuz: dict = {False: [], True: []}
    kayit = []
    for tur in range(_TUR):
        # SIRA HER TURDA TERSLENİR. Sabit sırada (hep önce kapalı, sonra açık) makinenin tur
        # boyunca ARTAN yükü sistematik olarak AÇIK kola yazılırdı — yani ölçüm, kolun maliyeti
        # yerine ölçüm sırasını ölçerdi. Ters çevirme bu kaymayı birinci mertebeden götürür.
        for acik_mi in ((False, True) if tur % 2 == 0 else (True, False)):
            havuz[acik_mi] += _dongu_olc(monkeypatch, sandbox_state, planli_acik=acik_mi)
        kayit.append({"sira": "kapali→acik" if tur % 2 == 0 else "acik→kapali",
                      "p95_kapali_ms": round(_p95(havuz[False][-_OLAY_N:]), 4),
                      "p95_acik_ms": round(_p95(havuz[True][-_OLAY_N:]), 4)})
    oran = _p95(havuz[True]) / _p95(havuz[False])
    # NEGATİF KONTROL — ALETİN ÇÖZÜNÜRLÜĞÜ (2026-08-16). Kapalı kolun kendi iki yarısı
    # birbirine bölünür: aynı kod, aynı yük, tek fark makinenin o anki gürültüsü. Bu oranın
    # 1,0'dan sapması, bu koşumda %10'luk bir etkiyi ÖLÇEBİLİR miyiz sorusunun cevabıdır.
    yari = len(havuz[False]) // 2
    kontrol = _p95(havuz[False][yari:]) / _p95(havuz[False][:yari])
    kontrol_sapma = abs(kontrol - 1.0)
    olcum = {"oran_havuzlanmis": round(oran, 4), "tavan": P95_TAVAN,
             "kontrol_orani": round(kontrol, 4), "kontrol_sapmasi": round(kontrol_sapma, 4),
             "p95_kapali_ms": round(_p95(havuz[False]), 4),
             "p95_acik_ms": round(_p95(havuz[True]), 4),
             "olay_n": len(havuz[True]), "sembol_n": _SEMBOL_N,
             "en_kotu_olay_ms": {"kapali": round(max(havuz[False]), 4),
                                 "acik": round(max(havuz[True]), 4)},
             "turlar": kayit}
    print("\nKILL#1 p95 ÖLÇÜMÜ:", json.dumps(olcum, ensure_ascii=False))
    # ÖLÇÜLEMEDİ ≠ KILL. Aletin kendi gürültüsü aradığımız etkiden BÜYÜKSE, "kol yavaşlattı"
    # hükmü kurulamaz — kurulursa ölçülmemiş bir şey ihlal sayılır (UYDURMA YASAĞI).
    #
    # NEDEN EKLENDİ — ÖLÇÜLDÜ, VARSAYILMADI (2026-08-16, bu konteyner): aynı makinede taban
    # (origin/main) ve dal DÖNÜŞÜMLÜ sırayla dörder kez koşturuldu.
    #     taban: 1,0539 · 0,8330 · 1,2590 · 1,1578  → ort 1,0759 · tavanı AŞAN 2/4
    #     dal:   0,9045 · 0,9442 · 1,0823 · 0,8363  → ort 0,9418 · tavanı AŞAN 0/4
    # Yani TABAN da tavanı aşıyor ve dal tabandan DAHA HIZLI ölçülüyor: kırmızı bir regresyonu
    # değil, ALETİN ÇÖZÜNÜRLÜĞÜNÜ raporluyordu. Sabit sıra kayması testin kendi A/B/B/A
    # serpiştirmesiyle zaten götürülmüştü; kalan şey konteynerin dakikalık yük varyansıdır.
    #
    # EŞİĞE DOKUNULMADI (CLAUDE.md kural 3 — kill-list dokunulmaz): `P95_TAVAN` hâlâ 1,10 ve
    # kontrol SIKI olduğunda aynen uygulanır; gerçek bir %10 regresyon bu makinede de düşer.
    # Eklenen tek şey ÜÇÜNCÜ bir hüküm: "ölçemedim" — ve o hüküm ADIYLA, sayısıyla görünür.
    if kontrol_sapma >= (P95_TAVAN - 1.0):
        pytest.skip(
            f"ÖLÇÜLEMEDİ — alet %10'luk etkiyi çözemiyor: negatif kontrol (kapalı kol ↔ kendisi) "
            f"{kontrol:.3f}× yani {kontrol_sapma:.1%} saparken aranan etki %{(P95_TAVAN-1)*100:.0f}. "
            f"Ölçülen oran {oran:.3f} bu koşumda HÜKÜM DEĞİLDİR. Ölçüm: {olcum}")
    assert oran <= P95_TAVAN, (
        f"planli kol p95 döngü süresini {oran:.3f}× yaptı (tavan {P95_TAVAN}) — kart kill#1: "
        f"kol kapatılır (negatif kontrol {kontrol:.3f}× = SIKI, yani alet bu etkiyi çözebiliyor). "
        f"Ölçüm: {olcum}")


# =================================================================================================
# 7) EŞİKLER KODA DEĞİL KARTA AİT
# =================================================================================================
def test_esikler_KARTTAN_gelir_ve_kod_onlari_degistiremez():
    """Ölçüm sonucu hoşa gitmediğinde değişecek olan şey eşik değil hükümdür (faz5_cikis deseni)."""
    kart = KART_YOLU.read_text()
    assert "card_id: EXE-2026-003" in kart and ish.KART == "EXE-2026-003"
    assert ish.IKINCIL_N_MIN == 40 and "n_min=40" in kart
    assert ish.PLANLI_PENCERE_SEANS == 20 and ish.PLANLI_HEDEF_DOLUM == 40
    assert ish.PLANLI_KILL_DOLUM == 10 and "< 10 planli dolum" in kart
    assert P95_TAVAN == 1.10 and "+%10" in kart
    assert ish.IKINCIL_CI == 0.95 and faz5_cikis.BOOTSTRAP_N == 10_000
    assert "B=10.000" in kart and "tarih-kümeli bootstrap" in kart
    # Kol adları da karttan: etiket sözlüğü sessizce değişirse iki hattın satırları eşleşmez.
    assert "kol: silahli" in kart and "kol: planli" in kart
    assert ish.KOL_SILAHLI == "silahli" and ish.KOL_PLANLI == "planli"


def test_defter_satiri_JSON_serilesebilir(sandbox_state, monkeypatch):
    """Uç bu satırı bir gün telden geçirirse numpy/NaN sızıntısı 500 üretirdi (v105 deseni)."""
    bc.set_clock(lambda: RTH)
    _kapilar_olculebilir()
    store.append_jsonl("trade_plans.jsonl", _plan())
    _bars_inject(monkeypatch)
    ic.consumer().on_barfeed_event({"syms": "AAA"})

    ham = (sandbox_state / ish.PLANLI_ORDERS_FILE).read_text().strip()
    json.loads(ham)
    json.dumps(ish.planli_kol_uretimi(), allow_nan=False)
    json.dumps(ish.golge_cf_eslestirme(), allow_nan=False, default=str)

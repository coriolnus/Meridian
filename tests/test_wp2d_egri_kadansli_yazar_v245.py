"""test_wp2d_egri_kadansli_yazar_v245.py — WP2-D: `equity_curve` ZİNCİRİNİN İKİ BACAĞI.

ÖLÇÜLEN ARIZA (canlı, 2026-08-13 · EDG-2026-036:174-178 · ROADMAP WP2-D):

  BACAK-2'NİN BOŞLUĞU — eğriye nokta ekleyen HİÇBİR kadanslı yazar yoktu. Yazanlar yalnız
  `run.replay_seed` (tohum, defterin tamamını tek seferde) ve `sermaye.uygula` (`points`e
  dokunmaz, zarfa reset işareti basar). Eğri 2026-07-20'de dondu, 24 gün tek nokta eklenmedi,
  pano P&L eğrisi hareketsiz kaldı.

  BACAK-1'İN ARIZASI — ve bu bir ÖNLEM DEĞİL ONARIMDIR: `ledgerstamp.seed_boundary()` tohum
  sınırını EĞRİNİN SON NOKTASINDAN okuyordu. Tohum 2026-08-13 18:54Z'de yenilendi, eğri
  yazılmadı, yani köken-sınırı YANLIŞ bir tarihi (2026-07-20) gösteriyordu. Üstelik bacak-2
  bacak-1'den ÖNCE yazılsaydı arıza büyürdü: eklenen her nokta sınırı bugüne taşır ve o günden
  sonraki HER canlı satır `replay_seed` damgalanırdı.

SIRA ZORUNLUYDU (kartın kendi kill şartı) ve bu dosya sırayı ÇİVİLER: bacak-1 (sınır artık
DONMUŞ reset işaretinden okunur — kaynak beyanı `kaynak` alanında) bacak-2'nin (kadanslı yazar)
ön koşuludur. İki bacağın KESİŞİMİ tek bir cümlede ölçülür: "eğriye nokta eklemek tohum sınırını
KAYDIRMAZ" — ve pozitif kontrolü yanındadır ("reset işareti değişirse sınır DEĞİŞİR"), yoksa test
ölü bir sabiti doğrulamış olurdu.

Bacak-1'in kendi ayrıntılı sözleşmesi `test_defter_kaynak_damgasi_v140.py`'nin BT-1 bölümündedir; burada
yalnız YAZARLA KESİŞEN yüzeyi ölçülür.

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` üzerinden koşar.
"""
from __future__ import annotations

import inspect
import pathlib

import pytest

from meridian import config, ledgerstamp, loop, recompute, sermaye, store
from meridian.score import START_EQUITY
from tests.conftest import make_bars

EQ = ledgerstamp.EQUITY


# =================================================================================================
# YARDIMCILAR
# =================================================================================================
def _islem(i: int, ts_close: str, pnl: float, kaynak: str = ledgerstamp.REPLAY_SEED) -> dict:
    return {"id": f"T{i:05d}", "ts_open": "2023-01-10", "ts_close": ts_close, "ticker": "AAA",
            "side": "long", "entry": 100.0, "exit": 101.0, "qty": 10, "r_multiple": 0.5,
            "pnl_pct": 0.01, "pnl_dollars": pnl, "costs": 5.0, "exit_reason": "target",
            "strategy_version": 4, "regime": "trend_up", "setup": "breakout_vcp", "bars_held": 5,
            "kaynak": kaynak}


def _isaret(egri_son: str, id_: str = "SR-20260801T151429") -> dict:
    """`sermaye.uygula`nın zarfa bastığı işaretin şekli (sermaye.py::uygula)."""
    return {"id": id_, "tarih": "2026-08-01T15:14:29+00:00", "tip": "paper_equity_reset",
            "onceki_deger": 94457.91, "yeni_deger": 100000.0,
            "egri_son_nokta": [egri_son, 94457.91], "gerekce": "fikstür"}


def _egri(son: str = "2026-07-20", deger: float = 94457.91, *, isaret: bool = True) -> None:
    eq = {"version": 4, "points": [["2023-01-12", 100000.0], [son, deger]]}
    if isaret:
        eq[sermaye.CURVE_MARK_KEY] = [_isaret(son)]
    store.write_json(EQ, eq)


def _pts() -> list:
    return store.read_json(EQ, {}).get("points") or []


def _rc(check: str) -> dict:
    return next(r for r in recompute.report()["rows"] if r["check"] == check)


def _olaylar(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


# =================================================================================================
# A — YAZARIN KENDİSİ (birim)
# =================================================================================================
def test_A_nokta_yazilir_ve_AYNI_GUN_IKINCI_KEZ_yazilmaz(sandbox_state):
    """İDEMPOTANLIK (kartın çivisi): koşum tekrarı / restart / elle tetik aynı güne ikinci bir
    satır YAZAMAZ. Canlıda döngü gün içinde defalarca dönüyor; her turda nokta eklense eğri
    seanslar yerine POLL'ları çizerdi ve 'günlük P&L' cümlesi anlamını kaybederdi."""
    _egri()
    m1 = loop._persist_equity_point("2026-08-14", 100500.0, {})
    assert m1["yazildi"] is True and m1["deger"] == 100500.0
    assert _pts()[-1] == ["2026-08-14", 100500.0] and len(_pts()) == 3
    assert m1["durum"] == "yazildi"
    m2 = loop._persist_equity_point("2026-08-14", 100500.0, {})
    assert m2["yazildi"] is False and "idempotent" in m2["neden"]
    assert len(_pts()) == 3, "aynı gün ikinci nokta yazıldı"
    # ÜÇÜNCÜ HÂL AYRI: "yazmadım çünkü ZATEN yazılı" ile "YAZAMADIM" aynı bayrağa düşemez —
    # pano bacağı (WP2-D bacak-3) bu ikisini farklı cümleyle anlatmak zorunda.
    assert m2["durum"] == "idempotent_atlandi"
    assert loop._persist_equity_point("2026-08-14", None, {})["durum"] == "yazilmadi"


def test_A_ayni_gun_DEGISEN_deger_YERINDE_tazelenir(sandbox_state):
    """Gün içinde öz sermaye değişirse nokta TAZELENİR, ÇOĞALMAZ: 'günde tek nokta' bir sayım
    kuralıdır, ilk ölçümü dondurma kuralı değil. Aksi hâlde eğri günün İLK turunun (çoğu zaman
    seans öncesi) sermayesini gösterirdi."""
    _egri()
    loop._persist_equity_point("2026-08-14", 100500.0, {})
    m = loop._persist_equity_point("2026-08-14", 100900.0, {})
    assert m["yazildi"] is True and m["tazelendi"] is True and m["durum"] == "tazelendi"
    assert len(_pts()) == 3 and _pts()[-1] == ["2026-08-14", 100900.0]


@pytest.mark.parametrize("eq_now", [None, float("nan"), float("inf"), "abc", {}])
def test_A_eq_OLCULEMEZSE_nokta_YAZILMAZ_ve_neden_KAYITLI(sandbox_state, eq_now):
    """UYDURMA YASAĞI'nın bu yüzdeki hâli: ölçülemeyen bir öz sermaye yerine SIFIR ya da BAYAT bir
    değer yazmak, eğriyi tam da onu okumak isteyen soruya ('P&L nereye gitti?') karşı yalancı
    yapardı. Satır yazılmaz — ve sessiz de kalmaz: makbuzda ve olay defterinde neden durur."""
    _egri()
    once = _pts()
    m = loop._persist_equity_point("2026-08-14", eq_now, {})
    assert m["yazildi"] is False and m["neden"]
    assert _pts() == once, "ölçülemeyen değer için eğriye yazıldı"
    assert _olaylar("equity_point_skipped"), "atlama SESSİZ kaldı"


def test_A_bicimsiz_TARIH_yazilmaz(sandbox_state):
    _egri()
    once = _pts()
    m = loop._persist_equity_point("bugün", 100500.0, {})
    assert m["yazildi"] is False and "tarih" in m["neden"]
    assert _pts() == once


def test_A_GERIYE_yazim_REDDEDILIR(sandbox_state):
    """Eğrinin son noktası seanstan İLERİDEYSE yazım reddedilir. Bayat bar ile koşan bir tur
    (ya da elle tetiklenmiş eski bir tarih) geçmişi sessizce yeniden yazamaz."""
    _egri(son="2026-08-20", deger=100000.0)
    once = _pts()
    m = loop._persist_equity_point("2026-08-14", 100500.0, {})
    assert m["yazildi"] is False and "GERİYE" in m["neden"]
    assert _pts() == once


def test_A_BOZUK_kuyrugun_ustune_yazilmaz(sandbox_state):
    """Son nokta ayrıştırılamıyorsa yazım durur: bozuk bir kuyruğun üstüne eklemek seriyi sessizce
    iki parçaya böler ve `recompute`in eğri kimliği bir daha asla ölçemezdi."""
    store.write_json(EQ, {"version": 4, "points": [["2023-01-12", 100000.0], "BOZUK"]})
    m = loop._persist_equity_point("2026-08-14", 100500.0, {})
    assert m["yazildi"] is False and "ayrıştırılamadı" in m["neden"]
    assert len(_pts()) == 2


def test_A_BOS_egriye_ilk_nokta_yazilabilir(sandbox_state):
    m = loop._persist_equity_point("2026-08-14", 100500.0, {})
    assert m["yazildi"] is True and _pts() == [["2026-08-14", 100500.0]]


def test_A_zarf_anahtarlari_KORUNUR(sandbox_state):
    """Yazar `points`e EKLER; zarfın öteki anahtarlarına DOKUNMAZ. `reset_isaretleri` orada
    yaşıyor ve bacak-1'in sınırı tam olarak o anahtardan okunuyor — ezilirse sınır kaybolurdu."""
    _egri()
    loop._persist_equity_point("2026-08-14", 100500.0, {})
    eq = store.read_json(EQ, {})
    assert eq["version"] == 4
    assert len(eq[sermaye.CURVE_MARK_KEY]) == 1
    assert eq[sermaye.CURVE_MARK_KEY][0]["egri_son_nokta"] == ["2026-07-20", 94457.91]


# =================================================================================================
# A2 — TABAN: NOKTA EĞRİNİN KENDİ TABANINDA YAZILIR
# =================================================================================================
def _ayrisik_dunya() -> dict:
    """Reset UYGULANMIŞ canlı hâlin küçük ölçeği — üç `recompute` kimliği de YEŞİL:
      trades Σ = −3.000 (tohum) + 500 (canlı) = −2.500 · beyanlı ofset = +3.000
      realized_pnl = 500 · cash = 100.000 + 500 = 100.500 · eğri sonu = cash − ofset = 97.500"""
    store.write_jsonl(ledgerstamp.LEDGER,
                      [_islem(i, f"2023-02-0{i+1}", -1000.0) for i in range(3)]
                      + [_islem(9, "2026-08-10", 500.0, ledgerstamp.LIVE_PAPER)])
    pf = {"cash": 100500.0, "realized_pnl": 500.0, "last_id": 4, "positions": {}, "armed": [],
          "pending_exits": {}, "last_date": "2026-08-13", "day_start_equity": 100500.0,
          "alpaca_submitted": [], "broker_rejected": [], "peak_equity": 100500.0,
          sermaye.RESET_KEY: [{"id": "SR-20260801T151429", "tarih": "2026-08-01T15:14:29+00:00",
                               "ofset": 3000.0, "gerekce": "fikstür"}]}
    store.write_json(sermaye.PORTFOLIO, pf)
    _egri(son="2026-08-13", deger=97500.0)
    return pf


def test_A2_nokta_BEYANLI_OFSET_dusulerek_yazilir(sandbox_state):
    """Eğri, kitabın tabanında DEĞİL KENDİ tabanında yaşar (reset `points`i silmez, kırılmayı
    `ofset` olarak BEYAN eder). Ham `eq_now` yazmak iki şeyi bozardı: recompute'un fark raporundaki "equity_curve_tail" satırı
    ofseti iki kez sayar (kalıcı kırmızı) ve eğri reset gününde ofset kadar SIÇRAR — hiç
    kazanılmamış bir günlük kâr çizilir."""
    pf = _ayrisik_dunya()
    eq_now = START_EQUITY + pf["realized_pnl"]          # broker.equity(): pozisyon yok
    m = loop._persist_equity_point("2026-08-14", eq_now, pf)
    assert m["yazildi"] is True
    assert m["eq_now"] == 100500.0 and m["ofset"] == 3000.0
    assert m["deger"] == 97500.0 != m["eq_now"], "ofset uygulanmadı — eğri tabanı sıçradı"


def test_A2_CIVI_recompute_egri_kimligi_YESIL_kalir(sandbox_state):
    """MUTABAKAT ÇİVİSİ: yazımdan SONRA `equity_curve_tail` (eğri sonu + beyanlı ofset == kitap
    nakdi) hâlâ ölçüyor ve yeşil. Bu satır kırmızıya dönseydi kadanslı yazar, sermaye
    ayrıştırmasının bütün mutabakat zeminini sessizce çürütmüş olurdu."""
    pf = _ayrisik_dunya()
    assert _rc("equity_curve_tail")["ok"] is True, "fikstür zaten kırmızı — test bir şey ölçmüyor"
    loop._persist_equity_point("2026-08-14", START_EQUITY + pf["realized_pnl"], pf)
    r = _rc("equity_curve_tail")
    assert r["ok"] is True, f"kadanslı yazar eğri kimliğini bozdu: {r['detail']}"
    assert r["a"] == pytest.approx(100500.0) and r["b"] == pytest.approx(100500.0)


def test_A2_OFSET_okunamazsa_nokta_YAZILMAZ(sandbox_state, monkeypatch):
    """Hangi tabanda yazılacağı ölçülemeyen bir nokta, eğriyi kimliğiyle birlikte bozar. Üçüncü
    hâl burada da geçerli: yaz-ve-umut-et yok, satır yazılmaz ve neden kaydedilir."""
    _ayrisik_dunya()
    monkeypatch.setattr(sermaye, "ofset", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("kitap okunamadı")))
    once = _pts()
    m = loop._persist_equity_point("2026-08-14", 100500.0, {})
    assert m["yazildi"] is False and "ofset" in m["neden"]
    assert _pts() == once and _olaylar("equity_point_skipped")


# =================================================================================================
# B — İKİ BACAĞIN KESİŞİMİ: YAZAR SINIRI KAYDIRMAZ
# =================================================================================================
def test_B_CIVI_kadansli_yazar_TOHUM_SINIRINI_kaydirmaz(sandbox_state):
    """BU DOSYANIN ASIL CÜMLESİ (bacak-1 ↔ bacak-2 kilidi). Yazarın KENDİSİ koşar (fikstür değil):
    30 seanslık nokta eklenir, tohum sınırı kıpırdamaz.

    POZİTİF KONTROL yanında: yeni bir reset İŞARETİ yazıldığında sınır DEĞİŞİR — yani ölçüm
    'her zaman aynı sabiti dönen' ölü bir fonksiyon değildir."""
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(i, f"2023-02-0{i+1}", -1000.0) for i in range(3)])
    _egri()
    once = ledgerstamp.seed_boundary()
    assert once["replay_end"] == "2026-07-20" and once["kaynak"] == ledgerstamp.KAYNAK_RESET
    for i in range(1, 31):
        assert loop._persist_equity_point(f"2026-09-{i:02d}", 100000.0 + i, {})["yazildi"] is True
    b = ledgerstamp.seed_boundary()
    assert b["replay_end"] == once["replay_end"], "30 nokta sonrası tohum sınırı KAYDI"
    assert b["kaynak"] == ledgerstamp.KAYNAK_RESET and b["n_equity_points"] == 32
    assert b["egri_son_nokta"] == "2026-09-30", "eski yolun değeri görünür (ama sınır DEĞİL)"
    # POZİTİF KONTROL
    eq = store.read_json(EQ, {})
    eq[sermaye.CURVE_MARK_KEY].append(_isaret("2026-09-30", id_="SR-20260930T000000"))
    store.write_json(EQ, eq)
    assert ledgerstamp.seed_boundary()["replay_end"] == "2026-09-30"


def test_B_IKI_YOL_AYRISIRSA_beyan_edilir(sandbox_state):
    """CANLIDA ÖLÇÜLEN HÂLİN FİKSTÜRÜ (2026-08-14): reset işareti 2026-08-01'de dondu ve eğrinin
    o anki son noktasını (2026-07-20) taşıyor; 2026-08-13 tohum YENİLEMESİ ise deftere en geç
    2026-07-24 kapanışlı satırlar yazdı. Donmuş sınır, tohumun gerçek penceresinden 4 gün geride.

    SIRA DEĞİŞMEZ (donma > tazelik — sınırın kaymaması köken defterinin ta kendisidir) AMA FARK
    SESSİZ KALAMAZ: tek bir tarihe bakan okuyucu iki kanıtın anlaştığını sanardı."""
    store.write_jsonl(ledgerstamp.LEDGER,
                      [_islem(0, "2023-02-01", -1000.0), _islem(1, "2026-07-24", -50.0)])
    _egri()                                    # işaret 2026-07-20'de donmuş
    b = ledgerstamp.seed_boundary()
    assert b["replay_end"] == "2026-07-20" and b["kaynak"] == ledgerstamp.KAYNAK_RESET
    assert b["yollar"] == {ledgerstamp.KAYNAK_RESET: "2026-07-20",
                           ledgerstamp.KAYNAK_DAMGA: "2026-07-24"}
    assert b["yollar_ayrisik"] is True and "AYRIŞMA" in b["neden"]
    # iki yol AYNI sayıyı verdiğinde bayrak inmeli — yoksa "ayrışma" gürültüye dönerdi
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(0, "2026-07-20", -1000.0)])
    b2 = ledgerstamp.seed_boundary()
    assert b2["yollar_ayrisik"] is False and "AYRIŞMA" not in b2["neden"]


def test_B_YEDEK_YOL_da_yazardan_ETKILENMEZ(sandbox_state):
    """Reset işareti HİÇ yazılmamış bir depoda sınır `trades.kaynak` damgasından okunur (kartın
    yazılı çaresi). O yol da eğriden bağımsızdır: yazar koşsa bile sınır damgada kalır — ve
    `kaynak` alanı hangi yolun konuştuğunu SÖYLER."""
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(i, f"2023-02-0{i+1}", -1000.0) for i in range(3)])
    _egri(isaret=False)
    once = ledgerstamp.seed_boundary()
    assert once["replay_end"] == "2023-02-03" and once["kaynak"] == ledgerstamp.KAYNAK_DAMGA
    loop._persist_equity_point("2026-09-01", 100500.0, {})
    b = ledgerstamp.seed_boundary()
    assert b["replay_end"] == "2023-02-03" and b["kaynak"] == ledgerstamp.KAYNAK_DAMGA


def test_B_yazar_CANLI_satirlari_TOHUMA_cevirmez(sandbox_state):
    """ARIZANIN SONUÇ CÜMLESİ: eski dünyada nokta eklendikten sonra sınır bugüne kayar ve
    `classify` canlı satırları `replay_seed` sayardı. Damgasız bir canlı satır üzerinde ölçülür —
    damgalı satır zaten kural-0'da korunur ve testi TRİVİYAL yapardı.

    İKİ ARKA UÇ, TEK YÖN: mtime imzası ayrışmışsa satır `live_paper` olur; imza (artık kadanslı
    yazar yüzünden GÜVENİLMEZ biçimde) 'toplu yazım' der görünürse sınıflandırıcı kendi kanıtını
    yalanlamaz ve `belirsiz` der. İkisi de DOĞRU tarafta: hiçbir koşulda canlı satır `replay_seed`
    olmaz."""
    import os
    store.write_jsonl(ledgerstamp.LEDGER,
                      [_islem(0, "2023-02-01", -1000.0),
                       {**_islem(9, "2026-08-10", 500.0), "kaynak": None}])
    _egri()
    loop._persist_equity_point("2026-08-14", 100500.0, {})
    dagilim = ledgerstamp.migrate(apply=False)["dagilim"]
    assert dagilim.get(ledgerstamp.REPLAY_SEED) == 1
    assert ledgerstamp.LIVE_PAPER in dagilim or ledgerstamp.BELIRSIZ in dagilim
    assert dagilim.get(ledgerstamp.REPLAY_SEED) == 1, "canlı satır TOHUM sayıldı"
    # imza ayrıştığında (defter, eğriden AYRI bir anda yazılmış) satır canlı okunur
    p = config.STATE / EQ
    eski = p.stat().st_mtime - 10 * ledgerstamp.BULK_WRITE_TOLERANCE_S
    os.utime(p, (eski, eski))
    assert ledgerstamp.migrate(apply=False)["dagilim"] == {ledgerstamp.REPLAY_SEED: 1,
                                                           ledgerstamp.LIVE_PAPER: 1}


# =================================================================================================
# C — DÖNGÜYE BAĞLANDI MI (gerçek `daily_cycle`)
# =================================================================================================
@pytest.fixture
def seeded(sandbox_state):
    import shutil

    import yaml
    repo = pathlib.Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


def _universe():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    return bars, idx


def test_C_daily_cycle_SEANS_NOKTASINI_yazar(seeded):
    """YASA 6'nın yazar tarafı: fonksiyon var olmak yetmez, DÖNGÜYE bağlı olmalı. Gerçek bir tur
    koşar; eğri o seansın noktasını kazanır ve makbuz hem dönüşte hem olay defterinde durur."""
    bars, idx = _universe()
    d = str(idx["date"].iloc[-1].date())
    ozet = loop.daily_cycle(bars, idx, on_date=d)
    assert ozet["status"] == "ok"
    mak = ozet["egri_nokta"]
    assert mak["yazildi"] is True and mak["tarih"] == d
    assert _pts()[-1][0] == d and _pts()[-1][1] == pytest.approx(ozet["equity"], abs=0.01)
    ev = _olaylar("daily_cycle")
    assert ev and ev[-1]["egri_nokta"]["yazildi"] is True


def test_C_ayni_gunu_IKI_KEZ_islemek_TEK_nokta_birakir(seeded):
    """Canlı desen: mid-cycle istisna sonrası her 300 sn'lik yeniden deneme aynı seansı yeniden
    işler (denetim #11'in işlem defterinde yaptığı şeyin eğri hâli)."""
    bars, idx = _universe()
    d = str(idx["date"].iloc[-1].date())
    loop.daily_cycle(bars, idx, on_date=d)
    n1 = len(_pts())
    loop.daily_cycle(bars, idx, on_date=d)
    assert len(_pts()) == n1, "aynı seans eğriye ikinci noktayı yazdı"
    assert sum(1 for p in _pts() if p[0] == d) == 1


def test_C_CIVI_yazar_daily_cycle_ICINDE_cagriliyor():
    """Statik çivi: davranış testi bir gün fikstür yüzünden atlanırsa bile bağın KOPARILDIĞI
    görünür kalsın (bu depoda 'fonksiyon var ama kimse çağırmıyor' ölçülmüş bir sınıftır)."""
    src = inspect.getsource(loop.daily_cycle)
    assert "_persist_equity_point(dstr, equity, meta)" in src


# =================================================================================================
# D — TÜKETİCİLER BOZULMADI
# =================================================================================================
def test_D_karne_sinirin_KAYNAGINI_tasir(sandbox_state):
    """`analytics.learning_scorecard` sınırı `defter["sinir"]`de servis ediyor (analytics.py::learning_scorecard) —
    sözleşme genişledi (yeni alanlar), daralmadı: eski anahtarlar yerinde."""
    from meridian import analytics
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(i, f"2023-02-0{i+1}", -1000.0) for i in range(3)])
    _egri()
    sinir = analytics.learning_scorecard()["defter"]["sinir"]
    for k in ("replay_end", "toplu_yazim", "mtime_delta_s", "n_equity_points", "guven", "neden",
              "kanit", "equity_ilk_nokta"):
        assert k in sinir, f"eski sözleşme alanı düştü: {k}"
    assert sinir["kaynak"] == ledgerstamp.KAYNAK_RESET and sinir["replay_end"] == "2026-07-20"


def test_D_seed_boundary_ROWS_ile_de_olculur(sandbox_state):
    """`_migrate_locked` sınırı ölçtüğü defterin KENDİSİNDEN türetir (kilidin içinde ikinci bir
    okuma = aynı kritik bölgede iki farklı an). İmza geriye uyumlu: argümansız çağrı diskten okur."""
    rows = [_islem(i, f"2023-02-0{i+1}", -1000.0) for i in range(3)]
    store.write_jsonl(ledgerstamp.LEDGER, rows)
    _egri(isaret=False)
    assert ledgerstamp.seed_boundary(rows)["replay_end"] == "2023-02-03"
    assert ledgerstamp.seed_boundary()["replay_end"] == "2023-02-03"
    assert ledgerstamp.seed_boundary([])["replay_end"] is None      # boş defter → sınır YOK


def test_D_kadansli_yazar_m2m_bacagini_YENIDEN_OLCULEBILIR_yapar(sandbox_state):
    """BEYAN EDİLMESİ GEREKEN YAN ETKİ — ÖLÇÜLDÜ, TAHMİN EDİLMEDİ.

    `analytics._realized_drawdown` seriyi KAPSADIĞI DÖNEMLE etiketler (fonksiyon gövdesi,
    analytics.py — satır çapası sembole çevrildi, 2026-08-23: K5 kaymasında bayatladı):
    eğrinin son noktası kitabın işlediği seansı KAPSAMIYORSA m2m bacağı 'dönem_dışı' sayılır,
    `gunluk_m2m_dd` None kalır ve `max_dd` bir ALT SINIR olur (Ç1, 2026-08-09 — bayat seriyle
    'kötüsü' hesaplanmaz). Kadanslı yazar tam o kapsamayı GERİ GETİRİR: aynı turda hem
    `portfolio.last_date` hem eğrinin son noktası o seansa oturur.

    SONUÇ: maks-düşüş ölçütünün girdisi 'bilinmiyor'dan 'ölçüldü'ye döner. Hiçbir eşiğe
    dokunulmadı — ama `edge_verdict`/`result_verdict` bu girdiyi okuyor, yani HÜKÜM OYNAYABİLİR.
    Sessiz bir yan etki olarak kalamazdı; çiviyle beyan ediliyor."""
    from meridian import analytics
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(i, f"2023-02-0{i+1}", -1000.0) for i in range(3)])
    store.write_json(sermaye.PORTFOLIO, {"cash": 97000.0, "realized_pnl": -3000.0, "positions": {},
                                         "last_date": "2026-08-14"})
    _egri()                                     # eğri 2026-07-20'de duruyor → kitabı KAPSAMIYOR
    once = analytics._realized_drawdown()
    assert once["m2m_durum"] == "donem_disi" and once["max_dd_alt_sinir"] is True
    assert once["gunluk_m2m_dd"] is None and once["bayat_seri_dd"] is not None
    loop._persist_equity_point("2026-08-14", 97000.0, {})
    sonra = analytics._realized_drawdown()
    assert sonra["m2m_durum"] == "olculdu" and sonra["max_dd_alt_sinir"] is False
    assert sonra["gunluk_m2m_dd"] is not None, "m2m bacağı hâlâ kör"
    assert sonra["seri_donem"][1] == "2026-08-14" == sonra["defter_seansi"]


def test_D_CIVI_egri_dosya_adi_TEK(sandbox_state):
    """Üç yazar, üç modül, TEK ad. İkiz literaller ayrışırsa iki ayrı dosya yazılır ve arıza
    'eğri neden güncellenmiyor' diye geri gelir."""
    assert loop.EQUITY_CURVE == ledgerstamp.EQUITY == sermaye.EQUITY == "equity_curve.json"

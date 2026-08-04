"""test_sermaye_beyani_v187.py — KİTABIN BEYANI SİLİNEMEZ (2026-08-04 "portföy sıfırlaması" vakası).

ÖLÇÜLEN KUSUR (research/olcumler/portfoy_sifirlama_2026-08-04/KOKNEDEN.md). 2026-08-01T15:14:29Z'de
operatörün koştuğu `meridian.sermaye --uygula` TAM BEYANLIYDI: kitap 100.000$ tabanına taşındı ve
gerekçesiyle birlikte `portfolio.sermaye_resetleri` kaydı yazıldı. Hafta sonundan sonraki İLK
noop-olmayan seansta `loop._save_broker` kitabı SABİT 13 ANAHTARLIK bir beyaz listeyle yeniden
serileştirdi — listede olmayan `sermaye_resetleri` SESSİZCE yok oldu. Beyan gidince
`recompute._sermaye_ofseti` 0,0'a düştü ve üç kimlik birden kırıldı (realized_pnl · cash_identity ·
equity_curve_tail) → 2026-08-04T01:16 MAKULLÜK alarmları.

Sınıf: *"defterin sahibi olmayan alanları, sahibiymiş gibi yeniden yazan tam-belge yazarı"*.

BU DOSYANIN TAŞIDIĞI SÖZLEŞMELER (hepsi davranış düzeyinde, hiçbiri metin eşleşmesi değil):
  D1  YAZAR YALNIZ SAHİP OLDUĞU ALANI YAZAR — `_save_broker` diskteki belgeyi YAMALAR; sahiplenmediği
      HİÇBİR anahtar (bugünkü beyan VE gelecekteki her beyan) yazımdan etkilenmez.
  D2  BEYAN YALNIZ EKLENEBİLİR (ratchet) — kayıt sayısı ya da ofset büyüklüğü düşen bir yazım
      kilit altında REDDEDİLİR ve alarm üretir. `watchdog.grant_amnesty` ailesinin aynı deseni:
      meşru küçülme YAZILI olmak zorundadır, sessizce düşemez.
  D3  EĞRİ ZARFI DA KORUNUR (aynı yasanın ikinci defteri) — `equity_curve` zarfının points-DIŞI
      anahtarları (reset işaretleri) yeni bir seri yazımında ezilmez.
  D4  ERKEN YAKALAMA — beyan defteri monotonluk tabanındadır: 1→0 düşüşü ÜÇ GÜN sonra üç kırık
      kimlik olarak değil, TEK döngüde bir gerileme satırı olarak görünür.

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` üzerinden koşar.
"""
from __future__ import annotations

import pytest

from meridian import broker as BR
from meridian import ledgerstamp, loop, recompute, sermaye, storage, store, watchdog
from meridian.broker import PaperBroker
from meridian.score import START_EQUITY

# Canlı vakanın GERÇEK kaydı (yedek DB'den birebir; KOKNEDEN §3). Sentetik bir kayıt da işi
# görürdü ama gerçek olan, testin neyi koruduğunu okuyana tek bakışta söyler.
KAYIT = {"id": "SR-20260801T151429+0000", "tarih": "2026-08-01T15:14:29+00:00",
         "onceki_cash": 94457.91, "yeni_cash": 100000.0, "ofset": 5542.09,
         "onceki_realized_pnl": -5542.09, "yeni_realized_pnl": 0.0,
         "gerekce": "operatör talimatı 2026-08-01: tohum-PnL gerçek-canlı sermayeden ayrıştırıldı",
         "arac": "meridian.sermaye"}


@pytest.fixture
def db_sandbox(sandbox_state):
    """SQLite arka ucu AÇIK sandbox (D3 orada yaşar; canlı defter 2026-07-31'den beri DB'dedir).
    Bağlantılar süreç havuzunda kalır — her test kendi tmp yoluna açar, tanıtıcıyı bırakmak
    uzun suite'te fd sızdırır."""
    storage.ensure_schema()
    yield sandbox_state
    storage.close_connections()


def _islem(i: int, pnl: float) -> dict:
    return {"id": f"T{i:05d}", "ts_open": "2023-01-10", "ts_close": f"2023-02-0{i + 1}",
            "ticker": "AAA", "side": "long", "entry": 100.0, "exit": 101.0, "qty": 10,
            "r_multiple": 0.5, "pnl_pct": 0.01, "pnl_dollars": pnl, "costs": 5.0,
            "exit_reason": "target", "strategy_version": 4, "regime": "trend_up",
            "setup": "breakout_vcp", "bars_held": 5, "kaynak": ledgerstamp.REPLAY_SEED}


def _tohumlu_dunya(n: int = 3, pnl_her: float = -1000.0) -> dict:
    """CANLI HÂLİN KÜÇÜK ÖLÇEĞİ: n tohum işlemi, kitap `run._reset_book_to`nun yazdığı gibi
    (nakit = başlangıç + Σ pnl), eğri o toplu yazımdan kalan noktalarla. Kimlikler bu dünyada
    YEŞİLDİR — testin ölçtüğü şey, bir kaydetme turunun onları kırıp kırmadığıdır."""
    realized = round(n * pnl_her, 2)
    cash = round(START_EQUITY + realized, 2)
    store.write_jsonl(ledgerstamp.LEDGER, [_islem(i, pnl_her) for i in range(n)])
    store.write_json(sermaye.EQUITY, {"version": 4, "points": [["2023-01-12", START_EQUITY],
                                                              ["2023-02-03", cash]]})
    pf = {"cash": cash, "realized_pnl": realized, "last_id": n, "positions": {}, "armed": [],
          "pending_exits": {}, "last_date": "2023-02-03", "day_start_equity": cash,
          "alpaca_submitted": [], "broker_rejected": [],
          "peak_equity": round(START_EQUITY + 2500, 2)}
    store.write_json(sermaye.PORTFOLIO, pf)
    store.write_json(watchdog.MONOTONIC_FILE, {"peak_equity": pf["peak_equity"],
                                               "book_date": "2023-02-03", "trades": n})
    return pf


def _alarmlar(n0: int = 0) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl")[n0:] if e.get("alarm")]


# =================================================================================================
# D1 — YAZAR YALNIZ SAHİP OLDUĞU ALANI YAZAR
# =================================================================================================
def test_D1_save_broker_YABANCI_anahtari_silmez(sandbox_state):
    """2026-08-04 REGRESYONUNUN KANITI (düzeltme öncesi KIRMIZI).

    Kitapta döngünün sahibi OLMADIĞI iki anahtar var: biri GERÇEK (sermaye beyanı), biri SENTETİK
    (`gelecekteki_beyan` — bugün var olmayan, yarın yazılacak her beyanın vekili). İkincisi
    bilerek burada: dar bir yama (`st["sermaye_resetleri"] = …`) birinciyi kurtarır ve SINIFI açık
    bırakırdı — bir sonraki beyan anahtarını yazan kişi aynı tuzağa düşerdi."""
    _tohumlu_dunya()
    pf = store.read_json(loop.PORTFOLIO, {})
    pf[sermaye.RESET_KEY] = [KAYIT]
    pf["gelecekteki_beyan"] = {"x": 1}
    store.write_json(loop.PORTFOLIO, pf)

    b, meta = loop._load_broker()
    loop._save_broker(b, meta)

    yeni = store.read_json(loop.PORTFOLIO, {})
    assert yeni.get(sermaye.RESET_KEY), "sermaye beyanı silindi — 2026-08-04 vakası"
    assert yeni[sermaye.RESET_KEY][0]["id"] == KAYIT["id"]
    assert yeni.get("gelecekteki_beyan"), "sahiplenilmemiş alan silindi (SINIF testi)"
    # …ve SAHİPLENİLEN alanlar GERÇEKTEN yazıldı: yama, dondurma değil.
    assert yeni["cash"] == b.cash and yeni["last_id"] == b._id
    assert yeni["last_date"] == meta["last_date"]


def test_D1_uctan_uca_kimlikler_bir_kaydetme_turundan_SONRA_yesil(sandbox_state):
    """UÇTAN UCA: reset → bir kaydetme turu → `recompute`in üç kimliği HÂLÂ tutmalı.

    Bu, canlıda 3 gün sonra üç kırmızı satır olarak görünen zincirin ta kendisidir: beyan
    kaybolursa ofset 0'a düşer ve üç kimlik birden kırılır."""
    _tohumlu_dunya()
    r = sermaye.uygula("uçtan uca kalıcılık sınaması — beyan bir kaydetme turunu atlatmalı")
    assert r["ok"] is True and r["yazildi"] is True

    loop._save_broker(*loop._load_broker())

    rows = {x["check"]: x["ok"] for x in recompute.report()["rows"]}
    for k in ("realized_pnl", "cash_identity", "equity_curve_tail"):
        assert rows.get(k) is not False, f"{k} reset SONRASI kırıldı — ofset beyanı kayboldu"
    assert sermaye.ofset() == r["ofset"] != 0.0        # beyan ölçülebilir hâlde duruyor


def test_D1_yama_SQLite_arka_ucunda_da_korur(db_sandbox):
    """VAKANIN GERÇEK ZEMİNİ: canlı kitap 2026-07-31'den beri SQLite'tadır ve `do_write_doc`
    `doc_json`u BÜTÜN OLARAK ezer (`ON CONFLICT … SET doc_json=excluded.doc_json`) — yani DB
    katmanında hiçbir birleştirme YOKTUR. Korunan alan ne varsa YAZARIN elinden gelir; bu testin
    ölçtüğü şey tam olarak odur."""
    assert store.db_backed(loop.PORTFOLIO) is True, "test DB arka ucunda koşmuyor"
    _tohumlu_dunya()
    pf = store.read_json(loop.PORTFOLIO, {})
    pf[sermaye.RESET_KEY] = [KAYIT]
    store.write_json(loop.PORTFOLIO, pf)

    b, meta = loop._load_broker()
    b.cash = 100000.0
    loop._save_broker(b, meta)

    yeni = store.read_json(loop.PORTFOLIO, {})
    assert yeni[sermaye.RESET_KEY][0]["id"] == KAYIT["id"]
    assert yeni["cash"] == 100000.0


def test_D1_sozluk_olmayan_belge_kitabi_yine_KALICI_kilar_ve_alarm_uretir(sandbox_state):
    """Diskteki belge sözlük DEĞİLSE (dış hasar) yama uygulanamaz. Yazımı sessizce ATLAMAK
    kitabın o turunu (nakit, pozisyonlar, dedup kümesi) kaybettirirdi; yapılan şey ALARM + tam
    yazımdır — korunacak yabancı anahtar zaten yok."""
    store.write_json(loop.PORTFOLIO, ["bozuk"])
    b = PaperBroker(START_EQUITY, 5, 0.0)
    b.cash = 99.0
    loop._save_broker(b, {"last_date": "2026-08-04"})

    doc = store.read_json(loop.PORTFOLIO, {})
    assert isinstance(doc, dict) and doc["cash"] == 99.0 and doc["last_date"] == "2026-08-04"
    assert _alarmlar(), "sözlük olmayan defter sessizce ezildi"


# =================================================================================================
# D2 — BEYAN YALNIZ EKLENEBİLİR (ratchet)
# =================================================================================================
def test_D2_beyan_olcusu_isaretten_bagimsiz_ve_kayit_basina_toplar():
    """Ölçü KAYIT BAŞINA MUTLAK toplamdır: kayıtlar yalnız EKLENDİĞİ için bu büyüklük monotondur.
    İşaretli toplam (`sermaye.ofset`) monoton DEĞİLDİR — ters işaretli ikinci bir reset onu
    küçültebilir ve ratchet o gün sahte alarm üretirdi."""
    pf = {sermaye.RESET_KEY: [{"id": "a", "ofset": 5542.09}, {"id": "b", "ofset": -5542.09}]}
    assert BR.beyan_olcusu(pf) == {"n": 2, "abs_ofset": 11084.18, "ids": ["a", "b"]}
    assert BR.beyan_olcusu({}) == {"n": 0, "abs_ofset": 0.0, "ids": []}
    assert BR.beyan_olcusu(None) == {"n": 0, "abs_ofset": 0.0, "ids": []}
    # ÖLÇÜLEMEYEN ofset UYDURULMAZ: kayıt SAYILIR (n), toplama 0 katkı verir.
    assert BR.beyan_olcusu({sermaye.RESET_KEY: [{"id": "c", "ofset": "yok"}]})["n"] == 1


def test_D2_kapi_yalnizca_GERILEMEDE_reddeder():
    a = {"n": 1, "abs_ofset": 5542.09, "ids": ["SR-1"]}
    assert BR.beyan_gerilemesi(a, a) is None                                   # aynı → geçer
    assert BR.beyan_gerilemesi(a, {"n": 2, "abs_ofset": 6000.0,
                                   "ids": ["SR-1", "SR-2"]}) is None           # büyüme → geçer
    assert BR.beyan_gerilemesi({"n": 0, "abs_ofset": 0.0, "ids": []}, a) is None
    assert BR.beyan_gerilemesi(a, {"n": 0, "abs_ofset": 0.0,
                                   "ids": []})["neden"] == "kayit_sayisi_dustu"
    assert BR.beyan_gerilemesi(a, {"n": 1, "abs_ofset": 100.0,
                                   "ids": ["SR-1"]})["neden"] == "ofset_kuculdu"
    # AYNI SAYI, BAŞKA KAYIT: beyan silinip yerine yenisi konmuş — sayı kapısı bunu görmez.
    g = BR.beyan_gerilemesi(a, {"n": 1, "abs_ofset": 5542.09, "ids": ["SR-X"]})
    assert g["neden"] == "kayit_kayboldu" and g["kayip_id"] == ["SR-1"]


def test_D2_diskten_silinmis_beyanin_UZERINE_yazim_REDDEDILIR_ve_alarm_uretir(sandbox_state):
    """RATCHET'İN KIRMIZI YOLU: döngü beyanı GÖRDÜ (meta), ama tur ortasında başka bir yazar onu
    diskten sildi. `_save_broker`ın o belgeyi kaydetmesi kaybı ÇİMENTOLAR — yazım reddedilir,
    kitap DOKUNULMAZ ve alarm operatöre kaybı AYNI DÖNGÜDE söyler.

    Kendi kendini iyileştirir: bir sonraki tur `meta`yı diskten yeniden okur, taban 0'a iner ve
    yazımlar sürer — yani kalıcı bir kilitlenme değil, TEK turluk bir fren + alarmdır."""
    _tohumlu_dunya()
    pf = store.read_json(loop.PORTFOLIO, {})
    pf[sermaye.RESET_KEY] = [KAYIT]
    store.write_json(loop.PORTFOLIO, pf)
    b, meta = loop._load_broker()                     # döngü beyanı BURADA gördü

    silen = store.read_json(loop.PORTFOLIO, {})       # başka bir tam-belge yazarı
    silen.pop(sermaye.RESET_KEY)
    silen["cash"] = 12345.0
    store.write_json(loop.PORTFOLIO, silen)
    n0 = len(store.read_jsonl("events.jsonl"))

    loop._save_broker(b, meta)

    sonra = store.read_json(loop.PORTFOLIO, {})
    assert sonra["cash"] == 12345.0, "yazım reddedilmedi — kitap beyansız hâliyle çimentolandı"
    a = _alarmlar(n0)
    assert a, "beyan gerilemesi SESSİZ geçti"
    assert a[-1]["yazar"] == "loop._save_broker" and a[-1]["neden"] == "kayit_sayisi_dustu"
    assert a[-1]["eski_n"] == 1 and a[-1]["yeni_n"] == 0


def test_D2_normal_tur_reddedilmez(sandbox_state):
    """POZİTİF KONTROL: ratchet'in bedeli ölçülür — beyan yerindeyken yazım GEÇER.
    (Kapı her turda reddetseydi kitap hiç kalıcı olmazdı ve testler yine 'kapı var' derdi.)"""
    _tohumlu_dunya()
    pf = store.read_json(loop.PORTFOLIO, {})
    pf[sermaye.RESET_KEY] = [KAYIT]
    store.write_json(loop.PORTFOLIO, pf)
    b, meta = loop._load_broker()
    b.cash = 98765.0
    n0 = len(store.read_jsonl("events.jsonl"))
    loop._save_broker(b, meta)
    assert store.read_json(loop.PORTFOLIO, {})["cash"] == 98765.0
    assert _alarmlar(n0) == []


# =================================================================================================
# D3 — AYNI YASA, İKİNCİ DEFTER: EĞRİ ZARFI
# =================================================================================================
def test_D3_egri_zarfi_yeniden_yazimda_KORUNUR(db_sandbox):
    """`run.py` eğriyi `{"version": …, "points": …}` ile TAM yazar; `reset_isaretleri` onun
    sahiplendiği bir anahtar DEĞİLDİR. Kusur LATENT'ti (henüz patlamadı): bir sonraki re-seed
    eğrinin beyanını da silecekti — `_touch`un `COALESCE` koruması `do_write_series` HER ZAMAN bir
    dict verdiği için hiçbir zaman devreye girmiyordu.

    KAPSAM DÜRÜSTLÜĞÜ: bu koruma SQLite arka ucundadır (canlı defter 2026-07-31'den beri orada).
    Dosya arka ucunda `store.write_json` belgeyi bütün olarak değiştirir; oradaki karşılığı
    yazarın kendi yamasıdır (D1 ile aynı reçete)."""
    assert store.db_backed(sermaye.EQUITY) is True, "test DB arka ucunda koşmuyor"
    store.write_json(sermaye.EQUITY, {"version": 4, "points": [["2026-07-20", 94457.91]],
                                      sermaye.CURVE_MARK_KEY: [{"id": KAYIT["id"]}]})
    store.write_json(sermaye.EQUITY, {"version": 4, "points": [["2026-07-20", 94457.91],
                                                               ["2026-07-31", 100000.0]]})
    eq = store.read_json(sermaye.EQUITY, {}) or {}
    assert eq.get(sermaye.CURVE_MARK_KEY), "eğri beyanı ikinci yazımda silindi"
    assert eq[sermaye.CURVE_MARK_KEY][0]["id"] == KAYIT["id"]
    # …ve sahiplenilen zarf anahtarı GÜNCELLENİR (birleştirme dondurma değildir)
    store.write_json(sermaye.EQUITY, {"version": 5, "points": []})
    eq2 = store.read_json(sermaye.EQUITY, {}) or {}
    assert eq2["version"] == 5 and eq2.get(sermaye.CURVE_MARK_KEY)


# =================================================================================================
# D4 — ERKEN YAKALAMA: BEYAN DEFTERİ MONOTONLUK TABANINDA
# =================================================================================================
def test_D4_beyan_gerilemesi_TEK_DONGUDE_bayraklanir(sandbox_state):
    """Canlıda kayıp 3 gün sonra ÜÇ kırık kimlik olarak göründü ve teşhis maliyeti bir kök-neden
    dosyasıydı. `len(sermaye_resetleri)` ve kayıt-başına mutlak ofset toplamı monoton-artan
    büyüklüklerdir: tabana bağlanınca 1→0 düşüşü BİR döngüde bir gerileme satırı olur."""
    ortak = {"last_date": "2026-07-31", "peak_equity": 100000.0}
    store.write_json(loop.PORTFOLIO, {**ortak, sermaye.RESET_KEY: [KAYIT]})
    ilk = watchdog.monotonicity_report(persist=True)
    assert ilk["ok"] is True

    store.write_json(loop.PORTFOLIO, dict(ortak))              # beyan silindi
    bad = watchdog.monotonicity_report(persist=True)
    assert bad["ok"] is False
    alanlar = {r["field"]: r for r in bad["regressions"]}
    assert {"sermaye_reset_n", "sermaye_ofset_abs"} <= set(alanlar)
    assert alanlar["sermaye_reset_n"]["was"] == 1 and alanlar["sermaye_reset_n"]["now"] == 0
    assert alanlar["sermaye_ofset_abs"]["was"] == KAYIT["ofset"]

"""test_dolum_geri_dolum_v475.py — TSK-182: geçmiş `live_paper` işlemlerinin dolum alanlarının
Alpaca kapalı-emir geçmişinden GERİ DOLUMU ölçülür (`ops/dolum_geri_dolum.py`).

BAĞLAM (Rol-1 ölçümü, A1 2026-09-13): `trades` tablosunda kaynak=`live_paper` 24 satırın 13'ünde
`extra_json.dolum_ts` YOK — 8 Ağustos işlemi yamayı hiç görmedi (görünürlük alanı `loop.
_exit_fill_yamasi` ile 08-2x'te doğdu), 5 Eylül işleminde `alpaca_fill_price` de yok (yama
koşmadı). EDG-2026-069 ADIM-0 bu yüzden düştü (n_uygun 11 < 30, eksik 0,54 > 0,30).

BU DOSYA BETİĞİN YAPTIĞINDAN ÇOK YAPMADIĞINI SINAR — canlı deftere yazan bir aracın en tehlikeli
hatası sessiz/yanlış yazımdır. Sentetik `trades` tabloları saf `sqlite3` ile `tmp_path`e kurulur;
`--db` doğrudan o yolu gösterir, yani DB tarafında canlı `state/`e hiçbir yazım YOKTUR. Betik
`meridian.obs`a ULAŞIR (`--uygula`nın tek olayı brief şartıdır), bu yüzden HER test `sandbox_state`
altındadır: olay defteri de tmp'ye düşer ve "kuru koşumda olay YOK" iddiası ölçülebilir hâle gelir.

K1  kuru koşum (varsayılan): DB bit-bit DEĞİŞMEZ, plan doğru, rc 0, `events.jsonl` HİÇ DOĞMAZ
K2  `--uygula`: boş giriş+çıkış alanları dolar, as-of damgası basılır, yedek VAR ve AÇILIYOR,
    rc 0, obs olayı TEK
K3  dolu alan ASLA ezilmez; broker farklı değer veriyorsa `ayrisma` sınıfıyla RAPORLANIR
K4  eşleşmeyen işlem ADIYLA raporlanır ve satırına DOKUNULMAZ (uydurma yok)
K5  doğrulama düşerse ROLLBACK — DB uygulama öncesiyle bit-bit aynı, rc 1
K6  broker erişilemez (`alpaca.transport()["ok"]=False`) → rc 3, DB değişmez, olay yok
K7  kullanım hatası: `--kuru`+`--uygula` çelişen çift → rc 2; DB yok → rc 2
K8  as-of damgası BİÇİMİ: `alpaca_orders_geri_dolum_<utc-iso>`
K9  `kaynak` kolonu DOKUNULMAZ; `replay_seed`/damgasız satır aday kümesine HİÇ girmez
K10 idempotans: ikinci `--uygula` yazacak bir şey bulmaz, DB değişmez, damga korunur
K11 çıkış "karar" kolu: `close_order_id` varsa `alpaca.order_by_id` yolu kullanılır
K12 gerçek `meridian.storage` şemasıyla kurulmuş DB'de de aynı sözleşme geçerli
K13 sayfalama: `--tavan` dolu sayfa geriye `until` ile sayfalanır; kapsanamayan pencere BEYANLI
K14 bozuk `extra_json` → satıra DOKUNULMAZ, adıyla raporlanır
"""
from __future__ import annotations

import json
import pathlib
import sqlite3

import pytest

from meridian.adapters import alpaca
from tests.conftest import betikten_modul_yukle

BETIK = pathlib.Path(__file__).resolve().parents[1] / "ops" / "dolum_geri_dolum.py"


def _mod():
    assert BETIK.exists(), f"betik YOK: {BETIK}"
    return betikten_modul_yukle(BETIK, "dolum_geri_dolum")


# ---- SENTETİK DB ---------------------------------------------------------------------------
_MINIMAL_DDL = """
CREATE TABLE trades (
    seq INTEGER PRIMARY KEY,
    id TEXT,
    plan_id TEXT,
    ticker TEXT,
    ts_open TEXT,
    ts_close TEXT,
    entry REAL,
    exit REAL,
    kaynak TEXT,
    extra_json TEXT
)
"""

_ALANLAR = ("seq", "id", "plan_id", "ticker", "ts_open", "ts_close", "entry", "exit",
            "kaynak", "extra_json")


def _db(tmp_path, satirlar: list[dict], ad: str = "meridian.db") -> pathlib.Path:
    yol = tmp_path / "veri" / ad
    yol.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(yol))
    try:
        conn.execute(_MINIMAL_DDL)
        for r in satirlar:
            conn.execute(
                f"INSERT INTO trades ({','.join(_ALANLAR)}) VALUES ({','.join('?' * len(_ALANLAR))})",
                tuple(r.get(a) for a in _ALANLAR))
        conn.commit()
    finally:
        conn.close()
    return yol


def _satir(seq: int, *, plan_id: str, ticker: str = "NUE", kaynak: str = "live_paper",
           extra: dict | None = None, extra_ham: str | None = None) -> dict:
    return {"seq": seq, "id": f"T{seq:05d}", "plan_id": plan_id, "ticker": ticker,
            "ts_open": "2026-08-06", "ts_close": "2026-08-20", "entry": 100.0, "exit": 110.0,
            "kaynak": kaynak,
            "extra_json": extra_ham if extra_ham is not None
            else (json.dumps(extra, ensure_ascii=False) if extra else None)}


def _oku_tum(yol: pathlib.Path) -> list[dict]:
    conn = sqlite3.connect(str(yol))
    try:
        cur = conn.execute("SELECT * FROM trades ORDER BY seq")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def _extra(yol: pathlib.Path, seq: int) -> dict:
    for r in _oku_tum(yol):
        if r["seq"] == seq:
            return json.loads(r["extra_json"]) if r["extra_json"] else {}
    raise AssertionError(f"seq={seq} DB'de yok")


# ---- SAHTE ALPACA -------------------------------------------------------------------------
def _bacak(fiyat, ts, status: str = "filled") -> dict:
    return {"status": status, "filled_avg_price": str(fiyat), "filled_at": ts,
            "type": "limit", "filled_qty": "10"}


def _emir(coid: str, *, oid: str = "o-1", status: str = "filled", fiyat=None, ts=None,
          legs: list | None = None, submitted: str = "2026-08-06T13:30:00Z") -> dict:
    return {"id": oid, "client_order_id": coid, "status": status,
            "filled_avg_price": (str(fiyat) if fiyat is not None else None),
            "filled_at": ts, "legs": list(legs or []), "submitted_at": submitted,
            "filled_qty": "10", "symbol": "NUE", "type": "limit"}


@pytest.fixture
def broker(monkeypatch):
    """Sahte Alpaca okuma ucu. `kur(emirler, tekil=…)` ile sayfa içeriği verilir; `cagrilar`
    listesinde `orders(**kw)` çağrılarının kwargs'ı BİRİKİR (sayfalama ölçülebilsin diye)."""
    durum = {"sayfalar": [[]], "tekil": {}, "cagrilar": [], "ok": True, "id_cagrilari": []}

    def _orders(**kw):
        durum["cagrilar"].append(dict(kw))
        i = len(durum["cagrilar"]) - 1
        return durum["sayfalar"][i] if i < len(durum["sayfalar"]) else []

    def _order_by_id(oid):
        durum["id_cagrilari"].append(str(oid))
        return durum["tekil"].get(str(oid))

    monkeypatch.setattr(alpaca, "orders", _orders)
    monkeypatch.setattr(alpaca, "order_by_id", _order_by_id)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": durum["ok"], "error": ""})
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)

    def kur(emirler: list, *, tekil: dict | None = None, sayfalar: list | None = None,
            ok: bool = True):
        durum["sayfalar"] = sayfalar if sayfalar is not None else [list(emirler)]
        durum["tekil"] = dict(tekil or {})
        durum["ok"] = ok
        return durum

    durum["kur"] = kur
    return durum


# ==============================================================================================
# K1 — KURU KOŞUM: DB BİT-BİT DEĞİŞMEZ, OLAY YOK
# ==============================================================================================
def test_K1_kuru_kosum_DB_ye_DOKUNMAZ_ve_OLAY_YAZMAZ(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    once = db.read_bytes()

    rc = m.main(["--db", str(db)])

    assert rc == 0
    assert db.read_bytes() == once, "kuru koşum DB'ye YAZDI"
    assert not (sandbox_state / "events.jsonl").exists(), \
        "kuru koşum canlı olay defterine YAZDI (obs kirlenmesi)"


def test_K1b_kuru_kosum_PLANI_hesaplar(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=200)
    (kalem,) = rapor["kalemler"]
    assert kalem["durum"] == "yazilacak"
    assert kalem["yazilacak"][m.ALAN_GIRIS_FIYAT] == 101.5
    assert kalem["yazilacak"][m.ALAN_GIRIS_TS] == "2026-08-06T13:31:00Z"
    assert kalem["yazilacak"][m.ALAN_CIKIS_FIYAT] == 111.25
    assert kalem["yazilacak"][m.ALAN_CIKIS_TS] == "2026-08-20T19:55:00Z"
    assert kalem["cikis_kaynak"] == "bacak"


# ==============================================================================================
# K2 — --uygula: BOŞ ALANLAR DOLAR, DAMGA BASILIR, YEDEK ALINIR, TEK OLAY
# ==============================================================================================
def test_K2_uygula_BOS_ALANLARI_DOLDURUR_ve_TEK_OLAY_YAZAR(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])

    rc = m.main(["--db", str(db), "--uygula"])

    assert rc == 0
    ex = _extra(db, 1)
    assert ex[m.ALAN_GIRIS_FIYAT] == 101.5
    assert ex[m.ALAN_GIRIS_TS] == "2026-08-06T13:31:00Z"
    assert ex[m.ALAN_CIKIS_FIYAT] == 111.25
    assert ex[m.ALAN_CIKIS_TS] == "2026-08-20T19:55:00Z"
    assert ex[m.ALAN_DAMGA].startswith(m.DAMGA_ONEKI)

    olaylar = [json.loads(s) for s in
               (sandbox_state / "events.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    assert len(olaylar) == 1, f"TEK olay bekleniyordu, {len(olaylar)} yazıldı"
    assert olaylar[0]["event"] == "dolum_geri_dolum"
    assert olaylar[0]["n_yazilan"] == 1
    assert olaylar[0]["n_eslesmeyen"] == 0


def test_K2b_uygula_YEDEK_alir_ve_yedek_ACILIR(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    assert m.main(["--db", str(db), "--uygula"]) == 0

    yedekler = sorted(db.parent.glob("meridian.db.*.bak"))
    assert len(yedekler) == 1, f"yedek alınmadı: {sorted(p.name for p in db.parent.iterdir())}"
    conn = sqlite3.connect(str(yedekler[0]))
    try:
        assert conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0] == 1
        ham = conn.execute("SELECT extra_json FROM trades WHERE seq=1").fetchone()[0]
    finally:
        conn.close()
    assert ham is None, "yedek UYGULAMA ÖNCESİ hâli taşımalı"


# ==============================================================================================
# K3 — DOLU ALAN EZİLMEZ + AYRIŞMA RAPORLANIR
# ==============================================================================================
def test_K3_dolu_alan_EZILMEZ(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE",
                               extra={"dolum_ts": "2026-08-20T19:00:00Z",
                                      "alpaca_fill_price": 109.0})])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])

    assert m.main(["--db", str(db), "--uygula"]) == 0

    ex = _extra(db, 1)
    assert ex["dolum_ts"] == "2026-08-20T19:00:00Z", "DOLU çıkış zamanı EZİLDİ"
    assert ex["alpaca_fill_price"] == 109.0, "DOLU çıkış fiyatı EZİLDİ"
    assert ex[m.ALAN_GIRIS_FIYAT] == 101.5, "BOŞ giriş alanı doldurulmadı"


def test_K3b_dolu_alan_FARKLIYSA_ayrisma_RAPORLANIR(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE",
                               extra={"dolum_ts": "2026-08-20T19:00:00Z",
                                      "alpaca_fill_price": 109.0})])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])

    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=200)
    (kalem,) = rapor["kalemler"]
    alanlar = {a["alan"] for a in kalem["ayrismalar"]}
    assert alanlar == {"dolum_ts", "alpaca_fill_price"}, kalem["ayrismalar"]
    for a in kalem["ayrismalar"]:
        assert a["sinif"] == "ayrisma"
        assert a["defterde"] != a["brokerda"]
    assert rapor["ozet"]["n_ayrisma"] == 2


def test_K3c_ayni_deger_AYRISMA_SAYILMAZ(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE",
                               extra={"dolum_ts": "2026-08-20T19:55:00Z",
                                      "alpaca_fill_price": 111.25})])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=200)
    assert rapor["ozet"]["n_ayrisma"] == 0


# ==============================================================================================
# K4 — EŞLEŞMEYEN ADIYLA
# ==============================================================================================
def test_K4_eslesmeyen_ADIYLA_raporlanir_ve_SATIRA_DOKUNULMAZ(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE"),
                        _satir(2, plan_id="P-2026-08-11-VLO", ticker="VLO")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    once = {r["seq"]: r for r in _oku_tum(db)}

    rc = m.main(["--db", str(db), "--uygula"])
    assert rc == 0

    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=200)
    eslesmeyen = [k for k in rapor["kalemler"] if k["durum"] == "eslesmedi"]
    assert [k["plan_id"] for k in eslesmeyen] == ["P-2026-08-11-VLO"]
    assert eslesmeyen[0]["ticker"] == "VLO"
    assert eslesmeyen[0]["neden"], "eşleşmeme nedeni BOŞ (uydurma yasağı: neden yazılır)"
    sonra = {r["seq"]: r for r in _oku_tum(db)}
    assert sonra[2] == once[2], "eşleşmeyen satıra YAZILDI"


# ==============================================================================================
# K5 — DOĞRULAMA DÜŞERSE ROLLBACK
# ==============================================================================================
def test_K5_dogrulama_duserse_ROLLBACK_ve_DB_BIT_BIT_AYNI(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE"),
                        _satir(2, plan_id="P-2026-08-11-VLO", ticker="VLO")])
    conn = sqlite3.connect(str(db))
    try:
        satirlar = m.oku_satirlar(conn)
        once = m.anlik(conn)
        # SABOTAJLI PLAN: ikinci kalem HAYALET bir `seq`e yazmaya çalışır (UPDATE hiçbir satırı
        # etkilemez). Doğrulama bunu YAKALAMALI ve BİRİNCİ kalemin yazımı da geri alınmalı —
        # yarım uygulanmış bir geri dolum, hiç uygulanmamış olandan daha kötüdür.
        plan = [{"seq": 1, "id": satirlar[0]["id"], "plan_id": satirlar[0]["plan_id"],
                 "ticker": "NUE", "yeni_extra": json.dumps({"dolum_ts": "x"}),
                 "yazilacak": {"dolum_ts": "x"}},
                {"seq": 999, "id": "T99999", "plan_id": "P-hayalet", "ticker": "VLO",
                 "yeni_extra": json.dumps({"dolum_ts": "y"}), "yazilacak": {"dolum_ts": "y"}}]
        sonuc = m.uygula_plan(conn, plan, once)
    finally:
        conn.close()

    assert sonuc["ok"] is False
    assert sonuc["hatalar"], "ROLLBACK nedeni ADSIZ"
    assert all(r["extra_json"] is None for r in _oku_tum(db)), "ROLLBACK yapılmadı, satırlar yazıldı"


def test_K5b_CLI_dogrulama_duserse_rc_1(tmp_path, sandbox_state, broker, monkeypatch):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    once = db.read_bytes()
    # Doğrulayıcıyı GERÇEKÇİ bir arıza gibi düşür: değişmez kırıldı → COMMIT edilmemeli.
    monkeypatch.setattr(m, "dogrula_sonrasi", lambda c, o, p: ["sentetik değişmez kırıldı"])

    rc = m.main(["--db", str(db), "--uygula"])

    assert rc == 1
    assert db.read_bytes() == once, "doğrulama düştüğü hâlde DB DEĞİŞTİ (rollback yok)"


# ==============================================================================================
# K6 — BROKER ERİŞİLEMEZ → rc 3
# ==============================================================================================
def test_K6_broker_erisilemez_rc_3_ve_YAZIM_YOK(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([], ok=False)
    once = db.read_bytes()

    rc = m.main(["--db", str(db), "--uygula"])

    assert rc == 3, "broker erişilemezken 3 dışında bir kod döndü"
    assert db.read_bytes() == once
    assert not (sandbox_state / "events.jsonl").exists()


def test_K6b_kimlik_yoksa_rc_3(tmp_path, sandbox_state, broker, monkeypatch):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)
    assert m.main(["--db", str(db)]) == 3


# ==============================================================================================
# K7 — KULLANIM HATALARI → rc 2
# ==============================================================================================
def test_K7_celisen_kip_bayragi_rc_2(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    assert m.main(["--db", str(db), "--kuru", "--uygula"]) == 2


def test_K7b_db_yoksa_rc_2(tmp_path, sandbox_state, broker):
    m = _mod()
    assert m.main(["--db", str(tmp_path / "yok.db")]) == 2


def test_K7c_gecersiz_tavan_rc_2(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    assert m.main(["--db", str(db), "--tavan", "0"]) == 2


def test_K7d_CLI_SOZLESMESI_argv_ve_main_blogu(tmp_path, sandbox_state):
    """Sözleşme KOMUT SATIRIDIR (`ops/` yasası): bayraklar argv'den çözülür ve `__main__` bloğu
    `main()`in çıkış kodunu SystemExit'e taşır. 18 çivi yeşilken `--uygula`nın sessizce yok
    sayıldığı vaka (2026-08-30) tam olarak bu katmanda yaşamıştı."""
    m = _mod()
    with pytest.raises(SystemExit) as e:
        m.main(["--help"])
    assert e.value.code == 0
    kaynak = BETIK.read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in kaynak
    assert "raise SystemExit(main())" in kaynak
    for bayrak in ("--db", "--kuru", "--uygula", "--baslangic", "--tavan"):
        assert f'"{bayrak}"' in kaynak, f"{bayrak} argparse sözleşmesinde YOK"


# ==============================================================================================
# K8 — AS-OF DAMGASI BİÇİMİ
# ==============================================================================================
def test_K8_damga_BICIMI_onek_arti_UTC_ISO(tmp_path, sandbox_state):
    import datetime as dt
    m = _mod()
    d = m.damga(dt.datetime(2026, 9, 13, 7, 45, 12, tzinfo=dt.timezone.utc))
    assert d == "alpaca_orders_geri_dolum_2026-09-13T07:45:12+00:00"
    assert d.startswith(m.DAMGA_ONEKI)
    # Damgasız yazım yok: üretilen damga her zaman önek + çözülebilir bir zaman taşır
    kalan = d[len(m.DAMGA_ONEKI):]
    assert dt.datetime.fromisoformat(kalan).tzinfo is not None


# ==============================================================================================
# K9 — `kaynak` KOLONU DOKUNULMAZ, live_paper DIŞI SATIR ADAY DEĞİL
# ==============================================================================================
def test_K9_kaynak_kolonu_DEGISMEZ(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    assert m.main(["--db", str(db), "--uygula"]) == 0
    (r,) = _oku_tum(db)
    assert r["kaynak"] == "live_paper"
    assert "kaynak" not in json.loads(r["extra_json"]), "`kaynak` extra_json'a SIZDIRILDI"


def test_K9b_live_paper_DISI_satir_ADAY_DEGIL(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2023-05-02-XYZ", kaynak="replay_seed"),
                        _satir(2, plan_id="P-2026-08-06-NUE", kaynak=None)])
    broker["kur"]([_emir("P-2023-05-02-XYZ", fiyat=50.0, ts="2023-05-02T13:31:00Z"),
                   _emir("P-2026-08-06-NUE", oid="o-2", fiyat=101.5, ts="2026-08-06T13:31:00Z")])
    once = db.read_bytes()
    rc = m.main(["--db", str(db), "--uygula"])
    assert rc == 0
    assert db.read_bytes() == once, "tohum/damgasız satır geri doldurma kapsamına ALINDI"


# ==============================================================================================
# K10 — İDEMPOTANS
# ==============================================================================================
def test_K10_ikinci_uygula_YAZMAZ_ve_damga_KORUNUR(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    assert m.main(["--db", str(db), "--uygula"]) == 0
    ilk_damga = _extra(db, 1)[m.ALAN_DAMGA]
    sonra_ilk = db.read_bytes()

    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    assert m.main(["--db", str(db), "--uygula"]) == 0
    assert db.read_bytes() == sonra_ilk, "ikinci koşum DB'yi DEĞİŞTİRDİ"
    assert _extra(db, 1)[m.ALAN_DAMGA] == ilk_damga


# ==============================================================================================
# K11 — ÇIKIŞ "KARAR" KOLU (close_order_id → order_by_id)
# ==============================================================================================
def test_K11_karar_kolu_order_by_id_ile_okur(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-09-08-BDX", ticker="BDX",
                               extra={"close_order_id": "c-77"})])
    broker["kur"]([_emir("P-2026-09-08-BDX", fiyat=201.0, ts="2026-09-08T13:31:00Z")],
                  tekil={"c-77": {"id": "c-77", "client_order_id": "alpaca-uretimi",
                                  "status": "filled", "filled_avg_price": "198.75",
                                  "filled_at": "2026-09-11T19:58:00Z", "legs": []}})

    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=200)
    (kalem,) = rapor["kalemler"]
    assert kalem["cikis_kaynak"] == "karar"
    assert kalem["yazilacak"][m.ALAN_CIKIS_FIYAT] == 198.75
    assert kalem["yazilacak"][m.ALAN_CIKIS_TS] == "2026-09-11T19:58:00Z"
    assert kalem["yazilacak"][m.ALAN_GIRIS_FIYAT] == 201.0
    assert broker["id_cagrilari"] == ["c-77"]


# ==============================================================================================
# K12 — GERÇEK ŞEMA UYUMU
# ==============================================================================================
def test_K12_gercek_storage_semasiyla_ayni_sozlesme(tmp_path, sandbox_state, broker):
    from meridian import storage
    m = _mod()
    yol = tmp_path / "gercek" / "meridian.db"
    yol.parent.mkdir(parents=True, exist_ok=True)
    conn = storage.connect(yol, create=True)
    storage.apply_schema(conn)
    conn.execute('INSERT INTO trades (id, plan_id, ticker, ts_open, ts_close, entry, "exit", '
                 'kaynak, extra_json) VALUES (?,?,?,?,?,?,?,?,?)',
                 ("T00900", "P-2026-08-06-NUE", "NUE", "2026-08-06", "2026-08-20", 100.0, 110.0,
                  "live_paper", None))
    storage.close_connections()

    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    assert m.main(["--db", str(yol), "--uygula"]) == 0
    ex = _extra(yol, 1)
    assert ex[m.ALAN_CIKIS_FIYAT] == 111.25
    assert ex[m.ALAN_GIRIS_TS] == "2026-08-06T13:31:00Z"


# ==============================================================================================
# K13 — SAYFALAMA
# ==============================================================================================
def test_K13_dolu_sayfa_GERIYE_sayfalanir(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    sayfa1 = [_emir(f"P-dolgu-{i}", oid=f"d-{i}", submitted="2026-08-25T13:30:00Z")
              for i in range(2)]
    sayfa2 = [_emir("P-2026-08-06-NUE", oid="o-9", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                    legs=[_bacak(111.25, "2026-08-20T19:55:00Z")], submitted="2026-08-06T13:30:00Z")]
    broker["kur"]([], sayfalar=[sayfa1, sayfa2])

    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=2)
    assert len(broker["cagrilar"]) == 2, broker["cagrilar"]
    assert broker["cagrilar"][0]["status"] == "closed"
    assert broker["cagrilar"][0]["nested"] is True
    assert broker["cagrilar"][0]["after"] == "2026-08-01"
    assert "until" not in broker["cagrilar"][0]
    assert broker["cagrilar"][1]["until"] == "2026-08-25T13:30:00Z"
    (kalem,) = rapor["kalemler"]
    assert kalem["durum"] == "yazilacak"
    assert rapor["pencere"]["kapsandi"] is True


def test_K13b_sayfa_tavani_asilirsa_pencere_BEYANLI(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE")])
    dolu = [[_emir(f"P-d-{s}-{i}", oid=f"d-{s}-{i}", submitted="2026-08-25T13:30:00Z")
             for i in range(2)] for s in range(m.SAYFA_TAVANI + 1)]
    broker["kur"]([], sayfalar=dolu)
    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=2)
    assert rapor["pencere"]["kapsandi"] is False
    assert rapor["pencere"]["neden"], "kapsanamayan pencere NEDENSİZ"
    assert len(broker["cagrilar"]) == m.SAYFA_TAVANI


# ==============================================================================================
# K14 — BOZUK extra_json
# ==============================================================================================
def test_K14_bozuk_extra_json_SATIRA_DOKUNULMAZ(tmp_path, sandbox_state, broker):
    m = _mod()
    db = _db(tmp_path, [_satir(1, plan_id="P-2026-08-06-NUE", extra_ham="{bozuk")])
    broker["kur"]([_emir("P-2026-08-06-NUE", fiyat=101.5, ts="2026-08-06T13:31:00Z",
                         legs=[_bacak(111.25, "2026-08-20T19:55:00Z")])])
    once = db.read_bytes()

    rc = m.main(["--db", str(db), "--uygula"])

    assert rc == 0
    assert db.read_bytes() == once, "bozuk extra_json taşıyan satır YENİDEN YAZILDI"
    rapor = m.calistir(db, uygula=False, baslangic="2026-08-01", tavan=200)
    (kalem,) = rapor["kalemler"]
    assert kalem["durum"] == "atlandi"
    assert "extra_json" in kalem["neden"]


# ==============================================================================================
# TEK-KAYNAK: OKUMA KURALLARI loop/alpaca'DAN İTHAL EDİLİR, KOPYALANMAZ
# ==============================================================================================
def test_okuma_kurallari_ITHAL_EDILIR_kopyalanmaz():
    """`_entry_fill_price` ve bacak-seçim ölçütü betikte YENİDEN YAZILMAZ: motor yamasıyla
    ayrışırsa geri dolum defteri motorun yazdığından farklı bir gerçek üretirdi."""
    from meridian import loop
    m = _mod()
    assert m.giris_dolum_fiyati is loop._entry_fill_price
    assert m.cikis_dolum_fiyati is alpaca.exit_fill_price
    assert m.cikis_dolum_zamani is alpaca.exit_fill_ts
    assert m.SAYFA_TAVANI == loop._EMIR_PENCERESI_SAYFA_TAVANI
    kaynak = BETIK.read_text(encoding="utf-8")
    assert "filled_avg_price" not in kaynak, \
        "dolum fiyatı alanı betikte ELLE okunuyor — okuma kuralı kopyalandı (tek-kaynak ihlali)"

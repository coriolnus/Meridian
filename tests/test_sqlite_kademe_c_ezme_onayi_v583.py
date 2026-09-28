"""v583 — TSK-020 Kademe C düzeltme turu 3 (F3): ezilecek satırlar KURU KOŞUDA görünür, `--uygula` AYRI onay ister.

BRIEF: scratchpad `tsk020c-tur3-brief.md` (Rol-1, 2026-09-28; Mercek-A ORTA-1, Rol-1 ENGEL saydı).

SORUN (tur 2'nin bıraktığı): kısıtlı geri alma (`--geri-al --varlik`) göç-sonrası DB satırlarını tabloda KANIT olarak bırakır;
sonraki `--uygula` o tabloyu "sil + yaz" ile kaynak dosyayla EZER. Sayı yalnız `apply()` ANINDA (COMMIT'ten SONRA) raporlanıyordu —
geri döndürülemez kayıp, önceden görünmüyordu.

ÇÖZÜM: `plan()` taşınacak (damgasız + kaynaklı) her varlık için tablodaki mevcut satırı `ezilecek` diye ölçer ve basar;
`apply()` böyle bir tablo varsa `--ezmeyi-onayla` (`ezmeyi_onayla=True`) olmadan HİÇBİR varlığı taşımadan reddeder (çıkış 2).
`--zorla` bu onayı VERMEZ — o canlı-süreç kapısının anahtarıdır; iki anlam tek bayrağa binmez. İlk göç (tablo yok/boş) ve
`zaten_tasindi` varlıklar etkilenmez.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from meridian import dbmigrate, storage, store

YENI = ("hypotheses.jsonl", "validation_ledger.jsonl")
ESKI = ("trades.jsonl", "trade_plans.jsonl", "scoreboard.json", "portfolio.json",
        "equity_curve.json", "shadow_books.json")
HYP, VAL = YENI

HYP_SATIRLAR = [
    {"id": f"H0000{i}", "ts": f"2026-08-0{i}T10:00:00+00:00", "variable": "entry.min_score",
     "old": 60, "new": 62.5, "rationale": "r", "predicted_direction": "up", "predicted_delta": 0.01,
     "confidence": 0.6, "regime": "trend_up", "source": "reflect", "version_from": 4,
     "version_to": None, "status": "proposed", "market_regime": "trend_up"}
    for i in range(1, 3)
]
VAL_SATIRLAR = [
    {"ts": f"2026-08-0{i}T10:00:00+00:00", "fingerprint": "fp-r1", "etiket": f"k={i}",
     "degisen_params": {"k": i}, "eval_regime": None, "oos_score": 0.1 * i, "incumbent_oos": 0.2,
     "passes": True, "gate_law": "para_v3", "fold_wins": "2/4", "tail_ok": True, "k_probes": i,
     "erosion_queries": 0, "n_trials": 10 + i, "oos_components": None, "oos_ozet": {},
     "sharpe_gozlem": 0.5, "dsr": None, "varyans_kaynagi": "ledger",
     "seri": [["2026-01-02", 1.5 * i]], "beyan": "b"}
    for i in range(1, 3)
]
GOC_SONRASI = dict(VAL_SATIRLAR[0], etiket="goc-sonrasi", ts="2026-09-29T10:00:00+00:00")
TRADE = {"id": "T00001", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAPL",
         "side": "long", "r_multiple": 1.5, "strategy_version": 4}


@pytest.fixture
def db_sandbox(sandbox_state, monkeypatch):
    monkeypatch.delenv("MERIDIAN_DB", raising=False)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: False)
    store._BAYAT_SUPURULDU.clear()
    yield sandbox_state
    storage.close_connections()
    store._BAYAT_SUPURULDU.clear()


def _yaz(state, ad, satirlar):
    (state / ad).write_text("".join(json.dumps(r) + "\n" for r in satirlar))


def _alti(state):
    _yaz(state, "trades.jsonl", [TRADE])
    _yaz(state, "trade_plans.jsonl", [{"id": "P-2026-01-02-AAPL", "date": "2026-01-02"}])
    for ad, doc in (("portfolio.json", {"cash": 1.0}), ("scoreboard.json", {"versions": {}}),
                    ("equity_curve.json", {"version": 1, "points": [["2026-01-02", 100.0]]}),
                    ("shadow_books.json", {"v": 1})):
        (state / ad).write_text(json.dumps(doc))


def _geri_alinmis(state):
    """Göç → göç-sonrası DB yazımı (VAL +1) → kısıtlı geri alma: iki tablo DOLU (HYP 2, VAL 3), damga YOK,
    kanonik dosyalar arşiv içeriğinde (HYP 2, VAL 2). Bir sonraki göç tam bu tabloları EZER."""
    _alti(state)
    _yaz(state, HYP, HYP_SATIRLAR)
    _yaz(state, VAL, VAL_SATIRLAR)
    assert dbmigrate.apply()["ok"] is True
    store.append_jsonl(VAL, GOC_SONRASI)
    r = dbmigrate.rollback_kisitli([HYP, VAL])
    assert r["ok"] is True and sorted(r["damgasi_kaldirilan"]) == sorted(YENI)


def _fotograf(state):
    """Tüm iz: sekiz varlığın damgası + tablo içeriği, şema sürümü, state/ dosya adları + içerikleri."""
    c = sqlite3.connect(str(storage.db_path()))
    try:
        meta = sorted(c.execute("SELECT entity, present, rev, n, migrated_at, source_digest "
                                "FROM entity_meta").fetchall())
        tablolar = {ad: c.execute(f"SELECT * FROM {storage.table_of(ad)} ORDER BY 1").fetchall()
                    for ad in ESKI + YENI}
        surum = c.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    finally:
        c.close()
    dosyalar = {p.name: p.read_bytes() for p in state.iterdir()
                if p.is_file() and p.name != "events.jsonl" and not p.name.startswith(storage.DB_NAME)}
    return {"meta": meta, "tablolar": tablolar, "surum": surum, "dosyalar": dosyalar}


# ---- 1. KURU KOŞU EZİLECEK SAYIYI GÖSTERİR --------------------------------------------------------
def test_kuru_kosu_ezilecek_satir_sayisini_gosterir(db_sandbox, capsys):
    _geri_alinmis(db_sandbox)
    plan = dbmigrate.plan()
    v = {x["varlik"]: x for x in plan["varliklar"]}
    assert v[HYP]["beklenen"] == "tasinacak" and v[HYP]["ezilecek"] == 2
    assert v[VAL]["beklenen"] == "tasinacak" and v[VAL]["ezilecek"] == 3
    assert all(v[ad]["ezilecek"] == 0 for ad in ESKI)
    assert {e["varlik"]: e["n"] for e in plan["ezilecek"]} == {HYP: 2, VAL: 3}
    capsys.readouterr()
    assert dbmigrate.main([]) == 0
    out = capsys.readouterr().out
    with capsys.disabled():
        print("\n" + out)
    assert "EZER" in out and "önce dışa al" in out and "--ezmeyi-onayla" in out
    assert any(s.split()[:1] == [VAL] and "EZİLECEK: 3" in s for s in out.splitlines())


# ---- 2. BAYRAKSIZ --uygula RET, HİÇBİR ŞEY DEĞİŞMEZ ---------------------------------------------
def test_bayraksiz_uygula_reddedilir_ve_hicbir_sey_degismez(db_sandbox, capsys):
    _geri_alinmis(db_sandbox)
    storage.close_connections()
    once = _fotograf(db_sandbox)
    capsys.readouterr()

    assert dbmigrate.main(["--uygula"]) == 2
    cikti = capsys.readouterr()
    assert "EZME" in (cikti.out + cikti.err) and "--ezmeyi-onayla" in (cikti.out + cikti.err)
    storage.close_connections()
    assert _fotograf(db_sandbox) == once, "reddedilen göç iz bıraktı"

    r = dbmigrate.apply()
    assert r["ok"] is False and r["ret"] == "EZME_ONAYI_YOK" and r["yazildi"] is False
    assert {e["varlik"]: e["n"] for e in r["ezilecek"]} == {HYP: 2, VAL: 3}
    assert "karantina" not in r
    storage.close_connections()
    assert _fotograf(db_sandbox) == once
    for ad in YENI:
        assert store.db_backed(ad) is False, ad


# ---- 3. BAYRAKLA GEÇER --------------------------------------------------------------------------
def test_bayrakla_gecer_ve_ezilen_raporlanir(db_sandbox, capsys):
    _geri_alinmis(db_sandbox)
    capsys.readouterr()
    assert dbmigrate.main(["--uygula", "--ezmeyi-onayla"]) == 0
    out = capsys.readouterr().out
    assert "EZİLDİ" in out
    for ad in YENI:
        assert store.db_backed(ad) is True and storage.meta(ad)["migrated_at"], ad
    assert [x["etiket"] for x in store.read_jsonl(VAL)] == ["k=1", "k=2"]
    r = dbmigrate.plan()
    assert r["ezilecek"] == [] and all(v["ezilecek"] == 0 for v in r["varliklar"])


def test_apply_bayrakla_ezilen_ile_ezilecek_ayni_olcum(db_sandbox):
    _geri_alinmis(db_sandbox)
    r = dbmigrate.apply(ezmeyi_onayla=True)
    assert r["ok"] is True
    assert {e["varlik"]: e["onceki_db_n"] for e in r["ezilen"]} == {HYP: 2, VAL: 3}
    p = {x["varlik"]: x for x in r["parite"]}
    assert p[VAL]["ezilen_db_satiri"] == 3 and p[VAL]["durum"] == "tasindi"


# ---- 4. İLK GÖÇ VE ESKİ ALTI ETKİLENMEZ ----------------------------------------------------------
def test_ilk_goc_bayraksiz_gecer_taze_db(db_sandbox):
    _alti(db_sandbox)
    _yaz(db_sandbox, HYP, HYP_SATIRLAR)
    _yaz(db_sandbox, VAL, VAL_SATIRLAR)
    assert all(v["ezilecek"] == 0 for v in dbmigrate.plan()["varliklar"])
    r = dbmigrate.apply()
    assert r["ok"] is True and sorted(r["tasinan"]) == sorted(ESKI + YENI) and r["ezilen"] == []


def test_ilk_goc_bayraksiz_gecer_v1_db(db_sandbox):
    """A1 hâli: şema v1, altı damgalı, iki defterin TABLOSU YOK → ezilecek 0, bayrak gerekmez."""
    _alti(db_sandbox)
    assert dbmigrate.apply()["ok"] is True
    storage.close_connections()
    con = sqlite3.connect(str(storage.db_path()), isolation_level=None)
    try:
        for ad in YENI:
            con.execute(f"DROP TABLE {storage.table_of(ad)}")
            con.execute("DELETE FROM entity_meta WHERE entity=?", (ad,))
        con.execute("DELETE FROM schema_version")
        con.execute("INSERT INTO schema_version(version, applied_at) VALUES (1, 0)")
    finally:
        con.close()
    _yaz(db_sandbox, HYP, HYP_SATIRLAR)
    _yaz(db_sandbox, VAL, VAL_SATIRLAR)
    plan = dbmigrate.plan()
    assert plan["ezilecek"] == [] and plan["tasinacak"] == 2
    assert dbmigrate.main(["--uygula"]) == 0
    assert store.db_backed(HYP) is True and store.db_backed(VAL) is True


def test_zaten_tasinmis_eski_alti_etkilenmez(db_sandbox):
    _alti(db_sandbox)
    _yaz(db_sandbox, HYP, HYP_SATIRLAR)
    _yaz(db_sandbox, VAL, VAL_SATIRLAR)
    assert dbmigrate.apply()["ok"] is True
    store.append_jsonl("trades.jsonl", dict(TRADE, id="T00002"))     # göç-sonrası yazım (tablo dolu)
    plan = dbmigrate.plan()
    assert all(v["ezilecek"] == 0 for v in plan["varliklar"])
    r = dbmigrate.apply()
    assert r["ok"] is True and "ret" not in r
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]


def test_kaynaksiz_tasinmis_eski_varligin_dolu_tablosu_da_korunur(db_sandbox):
    """Önceden var olan gizli yol: `kaynak_yok` diye taşınan (damgasız) eski varlık DB'ye yazılır; sonra kanonik dosyası
    doğarsa bir sonraki göç tabloyu dosyayla EZERDİ. Kural aynı: damgasız + dolu tablo → onaysız ret."""
    _alti(db_sandbox)
    (db_sandbox / "shadow_books.json").unlink()
    assert dbmigrate.apply()["ok"] is True                              # shadow_books: kaynak_yok
    store.write_json("shadow_books.json", {"v": "db-de-yasayan"})
    (db_sandbox / "shadow_books.json").write_text(json.dumps({"v": "bayat"}))
    v = {x["varlik"]: x for x in dbmigrate.plan()["varliklar"]}
    assert v["shadow_books.json"]["beklenen"] == "tasinacak" and v["shadow_books.json"]["ezilecek"] == 1
    r = dbmigrate.apply()
    assert r["ok"] is False and r["ret"] == "EZME_ONAYI_YOK"
    assert store.read_json("shadow_books.json", {}) == {"v": "db-de-yasayan"}


# ---- 5. --zorla EZMEYE İZİN VERMEZ; BAYRAK YALNIZ --uygula İLE ------------------------------------
def test_zorla_tek_basina_ezmeye_izin_vermez(db_sandbox, monkeypatch):
    _geri_alinmis(db_sandbox)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: True)       # zorla'nın açtığı kapı gerçekten kapalı
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: True)
    storage.close_connections()
    once = _fotograf(db_sandbox)
    assert dbmigrate.main(["--uygula", "--zorla"]) == 2
    storage.close_connections()
    assert _fotograf(db_sandbox) == once
    assert dbmigrate.main(["--uygula", "--zorla", "--ezmeyi-onayla"]) == 0
    assert store.db_backed(VAL) is True


def test_ezmeyi_onayla_uygula_olmadan_reddedilir(db_sandbox, capsys):
    _geri_alinmis(db_sandbox)
    for argv in (["--ezmeyi-onayla"], ["--geri-al", "--ezmeyi-onayla"], ["--durum", "--ezmeyi-onayla"]):
        assert dbmigrate.main(argv) == 2, argv
        assert "REDDEDİLDİ" in capsys.readouterr().err, argv
    assert store.db_backed(HYP) is False and storage.meta(HYP)["migrated_at"] is None

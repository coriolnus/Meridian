"""v579 — TSK-020 UYGULA-1 Kademe C: iki öğrenme defteri SQLite varlık kaydına girer + VARLIK BAZINDA açılış kapısı.

SPEC: `docs/TASARIM-SQLITE-KADEME-C-2026-09-28.md` (operatör ONAYLI 2026-09-28) — D1 (kayıt), D2 (kapı), D5 (tek kaynak).

NEYİ ÇİVİLER.
  D1 — `hypotheses.jsonl` + `validation_ledger.jsonl` `storage.ENTITIES`e "rows" türüyle girer; tipli kolonlar
       A1'de ÖLÇÜLMÜŞ anahtar evreninden (2026-09-28: 60 + 398 satır) seçilir; tipi karışık (`old`/`new`:
       int/float/None), iç içe ve seyrek alanlar `extra_json`da yaşar; `SCHEMA_VERSION` 1→2. Parite digesti
       ölçülmüş tip karışımıyla (int 3 ↔ float 3.0, None, iç içe sözlük, `-0.0`) BİREBİR tutar.
  D2 — R1'in (sessiz boş okuma penceresi) kapanışı: `storage.active(ad)` ŞEMA SONRADAN DOĞAN bir varlık
       (`storage.DAMGA_KAPILI`) için ANCAK `entity_meta.migrated_at` damgası doluysa True döner. Kod dağıtıldığı
       an iki defter DOSYADAN okunmaya devam eder; `dbmigrate --uygula`nın COMMIT'i onları DB'ye geçirir.
       Eski altı varlık kapıdan MUAFTIR — davranışları hiçbir ortamda değişmez (damgasız DB'de bile).
  dbmigrate artımlı koşu — A1'in ölçülmüş hâli (şema v1, altı varlık damgalı, iki defter dosyada) →
       altı `zaten_tasindi` + iki `tasindi`; parite turu DB'yi okur (dosya↔dosya kıyası SAHTE yeşil olurdu).
"""
from __future__ import annotations

import json
import math
import sqlite3
import time

import pytest

from meridian import config, dbmigrate, storage, store

YENI = ("hypotheses.jsonl", "validation_ledger.jsonl")
ESKI = ("trades.jsonl", "trade_plans.jsonl", "scoreboard.json", "portfolio.json",
        "equity_curve.json", "shadow_books.json")
HYP, VAL = YENI

# ---- A1 ÖLÇÜLMÜŞ EVRENİNİ TAKLİT EDEN SATIRLAR ----------------------------------------------------
# `old`/`new`: float34/int10/None16 (hyp) — üçü de burada; `version_to`: None58/int2; seyrek alanlar
# (`reject_reasons` liste, `backtest`/`realized_detail`/`vs_benchmark_at_ship` sözlük, `overfit_suspect`
# bool, `status_ts`/`note`/`outcome_ts` str, `realized_delta` float, `calibration_hit` bool).
HYP_SATIRLAR = [
    {"id": "H00001", "ts": "2026-08-01T10:00:00+00:00", "variable": "entry.min_score",
     "old": 60, "new": 62.5, "rationale": "skor tabanı gevşek", "predicted_direction": "up",
     "predicted_delta": 0.012, "confidence": 0.6, "regime": "trend_up", "source": "reflect",
     "version_from": 4, "version_to": None, "status": "rejected_by_backtest",
     "market_regime": "trend_up", "reject_reasons": ["oos_p", "fold_wins"],
     "backtest": {"oos_score": 0.1, "folds": [1, 2], "ship_modu": "paper", "dsr_dusuk": None}},
    {"id": "H00002", "ts": "2026-08-02T10:00:00+00:00", "variable": "exit.trail_r",
     "old": None, "new": 3, "rationale": "iz sürme", "predicted_direction": "down",
     "predicted_delta": -0.0, "confidence": 0.55, "regime": "chop", "source": "deterministic",
     "version_from": 4, "version_to": 5, "status": "promoted", "market_regime": "chop",
     "status_ts": "2026-08-03T00:00:00+00:00", "realized_delta": -0.0021,
     "realized_detail": {"market_regime": "chop", "n": 12, "ic": {"a": -0.0}},
     "calibration_hit": False, "outcome_ts": "2026-08-20T00:00:00+00:00",
     "vs_benchmark_at_ship": {"spy": 0.01}, "overfit_suspect": True, "note": "not"},
    # ÇEKİŞMELİ SATIR: REAL kolona int (`confidence: 1`), INTEGER kolona float (`version_from: 4.0`) —
    # tipli kolon DOĞRULUK kaynağı değildir; tip kaybı parite digestini düşürürdü.
    {"id": "H00003", "ts": "2026-08-05T10:00:00+00:00", "variable": "entry.min_score",
     "old": 3.0, "new": None, "rationale": "", "predicted_direction": "up",
     "predicted_delta": 0.0, "confidence": 1, "regime": "any", "source": "reflect",
     "version_from": 4.0, "version_to": None, "status": "proposed", "market_regime": "trend_up"},
]
VAL_SATIRLAR = [
    {"ts": "2026-08-01T10:00:00+00:00", "fingerprint": "fp-r1", "etiket": "entry.min_score=62.5",
     "degisen_params": {"entry.min_score": 62.5}, "eval_regime": None, "oos_score": 0.25,
     "incumbent_oos": 0.2, "passes": True, "gate_law": "para_v3", "fold_wins": "3/4",
     "tail_ok": True, "k_probes": 3, "erosion_queries": 7, "n_trials": 12,
     "oos_components": {"a": 1.0, "b": -0.0}, "oos_ozet": {"n": 80},
     "sharpe_gozlem": 0.8, "dsr": 0.4, "varyans_kaynagi": "ledger",
     "seri": [["2026-01-02", 1.5], ["2026-01-09", -0.0]], "beyan": "ölçüldü",
     "yasa_surumu": "para_v3", "oos_para": 0.1, "incumbent_para": None, "dd_ok": True,
     "candidate_dd": 0.05, "incumbent_dd": 0.06, "pencere_id": "R1"},
    {"ts": "2026-08-02T10:00:00+00:00", "fingerprint": "fp-r1", "etiket": "exit.trail_r=3",
     "degisen_params": {"exit.trail_r": 3}, "eval_regime": "trend_up", "oos_score": None,
     "incumbent_oos": None, "passes": False, "gate_law": "para_v3", "fold_wins": "1/4",
     "tail_ok": False, "k_probes": 0, "erosion_queries": 0, "n_trials": 13,
     "oos_components": None, "oos_ozet": {}, "sharpe_gozlem": None, "dsr": None,
     "varyans_kaynagi": None, "seri": [], "beyan": "ölçülemedi",
     "dd_mtm_durum": "ihlal_baglanmadi", "dd_mtm_bagli": False, "candidate_dd_mtm": 0.07,
     "incumbent_dd_mtm": 0.05, "ret_seri": [0.001, -0.0, 0.002], "ret_n": 3},
]

TRADE = {"id": "T00001", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAPL",
         "side": "long", "entry": 100.5, "exit": 110.25, "qty": 10, "r_multiple": 1.5,
         "strategy_version": 4}
PLAN = {"id": "P-2026-01-02-AAPL", "date": "2026-01-02", "ticker": "AAPL", "side": "long"}
BOOK = {"cash": 94457.91, "last_id": 95, "positions": {}}
SB = {"current_version": 3, "versions": {"3": {"n_trades": 95}}}
EQ = {"version": 4, "points": [["2026-01-02", 100000.0]]}
SHB = {"variants": {"v9": {"n": 3}}}


@pytest.fixture
def db_sandbox(sandbox_state, monkeypatch):
    """Sandbox + `MERIDIAN_DB` temiz + bağlantı ve süreç-ömürlü damga temizliği (iki yönde)."""
    monkeypatch.delenv("MERIDIAN_DB", raising=False)
    store._BAYAT_SUPURULDU.clear()
    yield sandbox_state
    storage.close_connections()
    store._BAYAT_SUPURULDU.clear()


def _jsonl(state, ad, satirlar):
    (state / ad).write_text("".join(json.dumps(r) + "\n" for r in satirlar))


def _alti_dosya(state):
    _jsonl(state, "trades.jsonl", [TRADE])
    _jsonl(state, "trade_plans.jsonl", [PLAN])
    for ad, doc in (("portfolio.json", BOOK), ("scoreboard.json", SB),
                    ("equity_curve.json", EQ), ("shadow_books.json", SHB)):
        (state / ad).write_text(json.dumps(doc, indent=2))


def _iki_dosya(state):
    _jsonl(state, HYP, HYP_SATIRLAR)
    _jsonl(state, VAL, VAL_SATIRLAR)


def _a1_benzeri(state):
    """A1'in 2026-09-28 ÖLÇÜLMÜŞ hâli: `schema_version` max=1, altı varlık `migrated_at` DAMGALI, iki
    öğrenme defteri DOSYADA (tabloları ve `entity_meta` satırları YOK). Kurgu: altısını taşı, sonra DB'yi
    v1'e indir (yeni tabloları ve damga satırlarını söküp sürümü 1'e çek) — v1 kodunun bıraktığı DB budur."""
    _alti_dosya(state)
    r = dbmigrate.apply()
    assert r["ok"] is True, r
    storage.close_connections()
    con = sqlite3.connect(str(storage.db_path()), isolation_level=None)
    try:
        for ad in YENI:
            con.execute(f"DROP TABLE IF EXISTS {storage.table_of(ad)}")
            con.execute("DELETE FROM entity_meta WHERE entity=?", (ad,))
        con.execute("DELETE FROM schema_version")
        con.execute("INSERT INTO schema_version(version, applied_at) VALUES (1, 0)")
    finally:
        con.close()
    _iki_dosya(state)
    # KURULUM ÇİPASI: A1 hâli gerçekten kuruldu mu (yoksa aşağıdaki yeşil kurulumdan gelirdi)
    con = sqlite3.connect(str(storage.db_path()))
    try:
        damgali = {r[0] for r in con.execute(
            "SELECT entity FROM entity_meta WHERE migrated_at IS NOT NULL")}
        tablolar = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        surum = con.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    finally:
        con.close()
    assert damgali == set(ESKI) and surum == 1
    assert not ({"hypotheses", "validation_ledger"} & tablolar)


def _olaylar(state, event):
    p = state / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines()
            if x.strip() and json.loads(x).get("event") == event]


# ---- D1: VARLIK KAYDI --------------------------------------------------------------------------
def test_kayit_iki_yeni_varlik_rows_turuyle_ve_sema_surumu_2():
    for ad in YENI:
        assert ad in storage.ENTITIES and storage.kind_of(ad) == "rows", ad
        assert ad in storage.ROW_ENTITIES
    assert storage.table_of(HYP) == "hypotheses"
    assert storage.table_of(VAL) == "validation_ledger"
    assert storage.SCHEMA_VERSION == 2
    # D2'nin TEK KAYNAĞI: kapıya tabi küme ŞEMADA SONRADAN DOĞANLARDIR — eski altısı MUAF
    assert set(storage.DAMGA_KAPILI) == set(YENI)
    assert not (set(storage.DAMGA_KAPILI) & set(ESKI))


def test_kolonlar_olculmus_evrenden_karisik_ic_ice_seyrek_alanlar_extra_jsonda():
    """Tipli kolon = A1'de HER satırda bulunan, tek tipli (None'a izinli) skaler alan. Tipi karışık
    (`old`/`new`), iç içe (liste/sözlük) ve seyrek (sonradan doğan) alanlar kolona ZORLANMAZ.
    TEK İSTİSNA `seri`: iç içe ama sözleşmede ZORUNLU → "JSON" kolon (watchdog `defter_sema_kapsami`)."""
    hyp = {c for c, _ in storage._COLS[HYP]}
    val = {c for c, _ in storage._COLS[VAL]}
    assert hyp == {"id", "ts", "variable", "rationale", "predicted_direction", "predicted_delta",
                   "confidence", "regime", "source", "version_from", "version_to", "status",
                   "market_regime"}
    assert val == {"ts", "fingerprint", "etiket", "eval_regime", "oos_score", "incumbent_oos",
                   "passes", "gate_law", "fold_wins", "tail_ok", "k_probes", "erosion_queries",
                   "n_trials", "sharpe_gozlem", "dsr", "varyans_kaynagi", "beyan", "seri"}
    assert dict(storage._COLS[VAL])["seri"] == "JSON"
    assert not ({"old", "new", "reject_reasons", "backtest", "realized_detail"} & hyp)
    assert not ({"degisen_params", "oos_components", "oos_ozet", "pencere_id",
                 "ret_seri", "ret_n", "yasa_surumu", "dd_ok"} & val)
    # sözleşmenin ZORUNLU alanlarının hepsi tipli kolon (watchdog eşdeğerlik çiftinin bu iki defter dilimi)
    from meridian import ledgers
    for ad in (HYP, VAL):
        assert set(ledgers.CONTRACTS[ad].required) <= {c for c, _ in storage._COLS[ad]}, ad


def test_json_kolonu_seri_sorgulanabilir_ve_birebir(db_sandbox):
    """`seri` gerçekten kolonda (extra_json'da değil) ve `json_extract` ile sorgulanır; gidiş-dönüş BİREBİR."""
    _alti_dosya(db_sandbox)
    _iki_dosya(db_sandbox)
    assert dbmigrate.apply()["ok"] is True
    c = storage.connect()
    rows = c.execute("SELECT seri, json_array_length(seri) AS n, extra_json FROM validation_ledger "
                     "ORDER BY seq").fetchall()
    assert [r["n"] for r in rows] == [2, 0]
    assert all("seri" not in json.loads(r["extra_json"] or "{}") for r in rows)
    assert [x["seri"] for x in store.read_jsonl(VAL)] == [VAL_SATIRLAR[0]["seri"], []]
    assert math.copysign(1.0, store.read_jsonl(VAL)[0]["seri"][1][1]) < 0


def test_parite_olculmus_tip_karisimiyla_birebir(db_sandbox):
    """Taze kurulum: sekiz varlık tek koşuda taşınır; iki yeni defter DB'den BİREBİR geri okunur."""
    _alti_dosya(db_sandbox)
    _iki_dosya(db_sandbox)
    r = dbmigrate.apply()
    assert r["ok"] is True, r.get("hata")
    esles = {p["varlik"]: p for p in r["parite"]}
    for ad in YENI:
        assert esles[ad]["durum"] == "tasindi" and esles[ad]["ok"] is True, esles[ad]
        assert esles[ad]["kaynak_digest"] == esles[ad]["db_digest"]
    assert esles[HYP]["n_db"] == len(HYP_SATIRLAR) and esles[VAL]["n_db"] == len(VAL_SATIRLAR)
    assert store.db_backed(HYP) is True and store.db_backed(VAL) is True
    h = store.read_jsonl(HYP)
    v = store.read_jsonl(VAL)
    assert dbmigrate.digest(h) == dbmigrate.digest(HYP_SATIRLAR)
    assert dbmigrate.digest(v) == dbmigrate.digest(VAL_SATIRLAR)
    # TİP AYRINTISI — digest'in neyi yakaladığını gözle de göster
    assert type(h[0]["old"]) is int and type(h[0]["new"]) is float
    assert "old" in h[1] and h[1]["old"] is None and "version_to" in h[0] and h[0]["version_to"] is None
    assert type(h[2]["old"]) is float and type(h[2]["confidence"]) is int
    assert type(h[2]["version_from"]) is float
    assert math.copysign(1.0, h[1]["predicted_delta"]) < 0
    assert h[1]["realized_detail"] == {"market_regime": "chop", "n": 12, "ic": {"a": -0.0}}
    assert v[1]["oos_score"] is None and "oos_score" in v[1] and v[1]["ret_seri"][1] == 0.0
    assert math.copysign(1.0, v[1]["ret_seri"][1]) < 0
    assert v[0]["passes"] is True and v[1]["passes"] is False
    # validation.ledger (son 200) DB'den aynı sırayla
    from meridian import validation
    assert [x["etiket"] for x in validation.ledger()] == [x["etiket"] for x in VAL_SATIRLAR]
    assert storage.schema_version() == storage.SCHEMA_VERSION == 2


# ---- D2: VARLIK BAZINDA AÇILIŞ KAPISI -----------------------------------------------------------
def test_damgasiz_yeni_varlik_db_varken_dosyadan_okunur(db_sandbox):
    """R1: kod dağıtıldığı an (A1: DB var, iki defter taşınmamış) okumalar DOSYADA kalır — boş defter yok."""
    _a1_benzeri(db_sandbox)
    for ad in YENI:
        assert store.db_backed(ad) is False, ad
    assert dbmigrate.digest(store.read_jsonl(HYP)) == dbmigrate.digest(HYP_SATIRLAR)
    assert len(store.read_jsonl(VAL, limit=200)) == len(VAL_SATIRLAR)
    # eski altısı DB'den (dosyaları `.migrated`)
    for ad in ESKI:
        assert store.db_backed(ad) is True, ad
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001"]
    # DB-DÜZEYİ SORU (`active()` adsız) anlamını korur
    assert storage.active() is True


def test_dbmigrate_artimli_alti_zaten_tasindi_iki_tasindi(db_sandbox):
    """D6-2'nin kuru koşusu + uygulaması A1 hâlinde: plan ÇÖKMEZ (tablo yok), iki `tasinacak` / altı
    `zaten_tasindi` der; uygulama yalnız ikisini taşır, damgayı basar ve okumayı DB'ye geçirir."""
    _a1_benzeri(db_sandbox)
    plan = dbmigrate.plan()
    beklenen = {v["varlik"]: v["beklenen"] for v in plan["varliklar"]}
    assert {ad: beklenen[ad] for ad in ESKI} == {ad: "zaten_tasindi" for ad in ESKI}
    assert {ad: beklenen[ad] for ad in YENI} == {ad: "tasinacak" for ad in YENI}
    assert plan["tasinacak"] == 2 and plan["zaten_tasindi"] == 6
    durum = {d["varlik"]: d for d in plan["db_durumu"]}
    for ad in YENI:
        assert durum[ad]["tablo_var"] is False and durum[ad]["n"] is None, durum[ad]
    assert durum["trades.jsonl"]["tablo_var"] is True and durum["trades.jsonl"]["n"] == 1
    assert storage.schema_version() == 1, "kuru koşu şemaya DOKUNDU"

    r = dbmigrate.apply()
    assert r["ok"] is True and r["yazildi"] is True, r.get("hata")
    esles = {p["varlik"]: p for p in r["parite"]}
    assert {ad: esles[ad]["durum"] for ad in ESKI} == {ad: "zaten_tasindi" for ad in ESKI}
    assert {ad: esles[ad]["durum"] for ad in YENI} == {ad: "tasindi" for ad in YENI}
    assert sorted(r["tasinan"]) == sorted(YENI)
    assert sorted(r["arsivlenen"]) == sorted(ad + storage.MIGRATED_SUFFIX for ad in YENI)
    assert storage.schema_version() == 2
    for ad in YENI:
        assert not (db_sandbox / ad).exists() and (db_sandbox / (ad + storage.MIGRATED_SUFFIX)).exists()
        assert store.db_backed(ad) is True
        assert storage.meta(ad)["migrated_at"] and storage.meta(ad)["source_digest"]
    assert dbmigrate.digest(store.read_jsonl(HYP)) == dbmigrate.digest(HYP_SATIRLAR)
    assert dbmigrate.digest(store.read_jsonl(VAL)) == dbmigrate.digest(VAL_SATIRLAR)
    # ikinci koşu idempotent: sekizi de zaten_tasindi
    r2 = dbmigrate.apply()
    assert r2["ok"] is True and r2["yazildi"] is False
    assert all(p["durum"] == "zaten_tasindi" for p in r2["parite"])


def test_parite_turu_dosyayi_degil_dbyi_okur(db_sandbox, monkeypatch):
    """EN TEHLİKELİ NOKTA: D2 damgasız varlığı dosyaya yönlendirir; parite turu da o yoldan okusaydı
    kaynak↔kaynak kıyaslanır ve kanıt SAHTE yeşil olurdu. Kanıt üretimi: DB yazımından tek satır düşer."""
    _a1_benzeri(db_sandbox)
    gercek = storage.do_replace_rows

    def _eksik(c, name, rows):
        return gercek(c, name, rows[:-1] if name == HYP else rows)

    monkeypatch.setattr(storage, "do_replace_rows", _eksik)
    r = dbmigrate.apply()
    assert r["ok"] is False and "PARİTE TUTMADI" in r["hata"] and HYP in r["hata"], r.get("hata")
    # DB bu koşudan önce vardı (altısı taşınmış) → KARANTİNA YOK, geri alma şemayı da götürdü
    assert r["karantina"]["yapildi"] is False and storage.db_path().exists()
    assert storage.schema_version() == 1
    assert store.db_backed(HYP) is False and store.db_backed("trades.jsonl") is True
    assert (db_sandbox / HYP).exists() and not (db_sandbox / (HYP + storage.MIGRATED_SUFFIX)).exists()
    assert dbmigrate.digest(store.read_jsonl(HYP)) == dbmigrate.digest(HYP_SATIRLAR)


def test_eski_alti_damgasiz_dbde_bile_davranis_degismez(db_sandbox):
    """`ensure_schema` ile doğan (hiç damgasız) DB: eski altısı BUGÜNKÜ gibi DB-otoriter; yalnız iki yeni
    defter dosyada kalır. (Genel kapı `test_bayat_defter_kalintisi_v234` gocsuz çivisini de kırardı.)"""
    storage.ensure_schema()
    for ad in ESKI:
        assert storage.active(ad) is True and store.db_backed(ad) is True, ad
    for ad in YENI:
        assert storage.active(ad) is False and store.db_backed(ad) is False, ad
    assert storage.active() is True
    # damgalı DB fikstürü: sekizi de DB
    storage.close_connections()
    _alti_dosya(db_sandbox)
    _iki_dosya(db_sandbox)
    storage.db_path().unlink()
    for ek in ("-wal", "-shm"):
        (db_sandbox / (storage.DB_NAME + ek)).unlink(missing_ok=True)
    assert dbmigrate.apply()["ok"] is True
    for ad in ESKI + YENI:
        assert store.db_backed(ad) is True, ad


def test_meridian_db_off_hepsi_dosyadan(db_sandbox, monkeypatch):
    _alti_dosya(db_sandbox)
    _iki_dosya(db_sandbox)
    assert dbmigrate.apply()["ok"] is True
    monkeypatch.setenv("MERIDIAN_DB", "off")
    for ad in ESKI + YENI:
        assert store.db_backed(ad) is False, ad
    assert storage.active() is False


def test_damga_baska_surecte_basilinca_bu_surec_gorur(db_sandbox):
    """Damgasız varlık için sonuç ÖNBELLEĞE ALINMAZ: göç başka bir süreçte (ayrı bağlantı) COMMIT
    edildiğinde bu süreç bir sonraki okumada DB'ye geçer — yeniden başlatma gerekmez."""
    _alti_dosya(db_sandbox)
    assert dbmigrate.apply()["ok"] is True          # iki yeni: kaynak_yok → tablo var, damgasız
    assert store.db_backed(HYP) is False
    assert store.read_jsonl(HYP) == []              # dosya yok → boş (dosya dünyası)
    # BAŞKA SÜREÇ: ayrı bağlantı satırı yazar + damgayı basar (dbmigrate'in yaptığının özü)
    vals, extra = storage._row_to_cols(HYP, HYP_SATIRLAR[0])
    cols = [c for c, _ in storage._COLS[HYP]]
    con = sqlite3.connect(str(storage.db_path()), isolation_level=None)
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute(f'INSERT INTO hypotheses ({",".join(chr(34) + c + chr(34) for c in cols)},extra_json) '
                    f'VALUES ({",".join("?" * (len(cols) + 1))})', (*vals, extra))
        con.execute("UPDATE entity_meta SET present=1, n=1, rev=rev+1, migrated_at=?, source_digest='x' "
                    "WHERE entity=?", (time.time(), HYP))
        con.execute("COMMIT")
    finally:
        con.close()
    assert store.db_backed(HYP) is True, "damgasız sonuç önbellekte kaldı — göçü göremedi"
    assert [r["id"] for r in store.read_jsonl(HYP)] == ["H00001"]


def test_acik_transaction_icindeki_damga_onbellege_girmez(db_sandbox):
    """Aynı bağlantı kendi COMMIT edilmemiş yazımını görür. Transaction içinde sorulan damga
    önbelleğe alınırsa ROLLBACK'ten sonra süreç SİLİNMİŞ bir gerçeğe göre DB'den (boş) okurdu."""
    _alti_dosya(db_sandbox)
    assert dbmigrate.apply()["ok"] is True
    c = storage.connect()
    with storage._GUARD:
        c.execute("BEGIN IMMEDIATE")
        try:
            storage.mark_migrated(HYP, digest="x", conn=c)
            storage.active(HYP)                     # ne dediği önemli değil — önbelleğe yazmamalı
        finally:
            c.execute("ROLLBACK")
    assert storage.active(HYP) is False and store.db_backed(HYP) is False


def test_bedel_damgali_varlik_sorgusuz_damgasiz_her_cagrida_tek_sorgu(db_sandbox):
    """Bedel yasası (D2 §6-c): damga dolunca bir daha SORULMAZ; damgasız varlık her okumada TEK
    `entity_meta` sorgusu öder (göç başka süreçte olur, görülmesi gerekir). Süreler bilgi için basılır."""
    _alti_dosya(db_sandbox)
    _jsonl(db_sandbox, HYP, HYP_SATIRLAR)            # yalnız HYP taşınır; VAL kaynak_yok → damgasız
    assert dbmigrate.apply()["ok"] is True
    c = storage.connect()
    sorgular: list[str] = []
    c.set_trace_callback(lambda s: sorgular.append(s))
    try:
        storage.active(HYP)                          # ısınma: damga önbelleğe girer
        sorgular.clear()
        t0 = time.perf_counter()
        for _ in range(200):
            assert storage.active(HYP) is True
        t_damgali = (time.perf_counter() - t0) / 200
        assert sorgular == [], sorgular[:3]
        t0 = time.perf_counter()
        for _ in range(200):
            assert storage.active(VAL) is False
        t_damgasiz = (time.perf_counter() - t0) / 200
        assert len([s for s in sorgular if "entity_meta" in s]) == 200
        assert len(sorgular) == 200
    finally:
        c.set_trace_callback(None)
    print(f"\n[bedel] active(): damgalı {t_damgali * 1e6:.1f} µs/çağrı · damgasız {t_damgasiz * 1e6:.1f} µs/çağrı")


def test_suzgec_damgasiz_yeni_varligin_dosyasini_gocsuz_diye_beyan_etmez(db_sandbox):
    """Bayat-defter süzgeci DB-otoriter varlıkların işidir. A1'de dağıtım→göç arasında iki defterin
    dosyası OTORİTERDİR; `db_aktif_kanonik_dosya_gocsuz` ("dosya store okuyucularına görünmez") demek
    YANLIŞ bir beyan olurdu ve dosya yerinde kalmalıdır."""
    _a1_benzeri(db_sandbox)
    store._BAYAT_SUPURULDU.clear()
    assert store.db_backed("trades.jsonl") is True   # süzgeç tetiği
    assert _olaylar(db_sandbox, "db_aktif_kanonik_dosya_gocsuz") == []
    assert _olaylar(db_sandbox, "bayat_defter_arsivlendi") == []
    for ad in YENI:
        assert (db_sandbox / ad).exists(), ad


def test_damgali_yeni_varligin_bayat_kanonik_dosyasi_arsive_cekilir(db_sandbox):
    """Simetri: göç SONRASI yeniden doğan kanonik dosya (DB-otoriter varlık) süzgeçten kaçamaz."""
    _alti_dosya(db_sandbox)
    _iki_dosya(db_sandbox)
    assert dbmigrate.apply()["ok"] is True
    _jsonl(db_sandbox, VAL, VAL_SATIRLAR[:1])        # bayat kalıntı
    store._BAYAT_SUPURULDU.clear()
    assert len(store.read_jsonl(VAL)) == len(VAL_SATIRLAR)   # DB'den, dosyadan değil
    assert not (db_sandbox / VAL).exists()
    olay = _olaylar(db_sandbox, "bayat_defter_arsivlendi")
    assert len(olay) == 1 and [k["dosya"] for k in olay[0]["arsivlenen"]] == [VAL]


def test_cli_operatorun_kostugu_bicimde_durum_kuru_kosu_uygula(db_sandbox, capsys, monkeypatch):
    """D6-2'yi operatörün koşacağı BİÇİMDE (komut satırı sözleşmesi, `main(argv)`) A1 hâlinde koşar:
    `--durum` v1 DB'de ÇÖKMEZ, kuru koşu iki `tasinacak` / altı `zaten_tasindi` basar, `--uygula` iki
    `tasindi` + arşiv, sonra `--durum` şema 2. Basılan metin `-s` ile devir raporuna girer."""
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: False)   # tur 2 F2 kapısı (v582)
    _a1_benzeri(db_sandbox)
    capsys.readouterr()                       # kurulumun obs satırları (obs olayları stdout'a da düşer)

    def _json_blok(metin):
        """`--durum` çıktısı `indent=1` JSON bloğudur; obs'un tek satırlık olay yankıları ayıklanır."""
        return json.loads(metin[metin.index("{\n"):])

    assert dbmigrate.main(["--durum"]) == 0
    durum = _json_blok(capsys.readouterr().out)
    assert durum["sema_surumu"] == 1
    d = {x["varlik"]: x for x in durum["durum"]}
    assert all(d[ad]["tablo_var"] is False and d[ad]["n"] is None for ad in YENI)

    assert dbmigrate.main([]) == 0
    kuru = capsys.readouterr().out
    with capsys.disabled():
        print("\n" + kuru)
    assert "KURU KOŞU" in kuru and "şema sürümü: 1" in kuru
    assert "taşınacak varlık: 2, zaten taşınmış: 6" in kuru
    satirlar = kuru.splitlines()
    for ad in YENI:
        assert any(s.split()[:1] == [ad] and "tasinacak" in s for s in satirlar), ad
    for ad in ESKI:
        assert any(s.split()[:1] == [ad] and "zaten_tasindi" in s for s in satirlar), ad
    assert storage.schema_version() == 1, "kuru koşu yazdı"

    assert dbmigrate.main(["--uygula"]) == 0
    uyg = capsys.readouterr().out
    with capsys.disabled():
        print(uyg)
    assert "UYGULANDI" in uyg
    for ad in YENI:
        assert any(s.strip().startswith(f"OK {ad}") and "tasindi" in s and "zaten" not in s
                   for s in uyg.splitlines()), ad
    assert "hypotheses.jsonl.migrated" in uyg and "validation_ledger.jsonl.migrated" in uyg

    assert dbmigrate.main(["--durum"]) == 0
    sonra = _json_blok(capsys.readouterr().out)
    assert sonra["sema_surumu"] == 2
    d = {x["varlik"]: x for x in sonra["durum"]}
    assert d[HYP]["n"] == len(HYP_SATIRLAR) and d[VAL]["n"] == len(VAL_SATIRLAR)
    assert all(d[ad]["migrated_at"] and d[ad]["db_digest"] == d[ad]["kaynak_digest"] for ad in YENI)


# ---- D5: "altı" SAYISI TEK KAYNAKTAN ------------------------------------------------------------
def test_varlik_sayisi_kayittan_turer(capsys, db_sandbox):
    with pytest.raises(SystemExit):
        dbmigrate.main(["--help"])
    yardim = capsys.readouterr().out
    assert f"{len(storage.ENTITIES)} varlık" in yardim and "(6 varlık)" not in yardim
    # başarısız migrasyonun beyanı da kayıttan türer (taze DB → karantina dalı)
    (db_sandbox / "portfolio.json").write_text("{ bozuk")
    r = dbmigrate.apply()
    assert r["ok"] is False
    assert f"{len(storage.ENTITIES)} defter" in r["karantina"]["beyan"]
    assert "altı defter" not in r["karantina"]["beyan"]

"""v581 — TSK-020 Kademe C D4: kum havuzu maddeleştirmesi — R3 "kum havuzları geçmişi sessizce kaybeder".

SPEC: `docs/TASARIM-SQLITE-KADEME-C-2026-09-28.md` D4 (operatör ONAYLI 2026-09-28).

R3: sprint kum havuzu `meridian.db`'yi BİLEREK kopyalamaz (izolasyon — `sprint.SKIP_COPY`) ve dosyayla çalışır.
Göçten sonra canlıdaki `validation_ledger.jsonl` `.migrated` adını alır → kum havuzunda defter YOK → kapının DSR
deneme örneklemi (`validation.ledger`, son 200) boş başlar, PBO tabanı sıfırlanır; uyarı yok.

D4: kum havuzu kurulurken, kapıya tabi (`storage.DAMGA_KAPILI`) bir varlık canlıda DB'den okunuyorsa ve kum
havuzu DB TAŞIMIYORSA, canlı DB'nin o anki içeriği kum havuzuna KANONİK dosya adıyla yazılır. Sonra sprint'in
kendi sıfırlaması (`hypotheses.jsonl`) bugünkü gibi üstüne yazar. Eski altı varlığa UYGULANMAZ (tasarım D4
açık sorusu — ayrı ölçüm kalemi).

ÖLÇÜM FARKI (uygulayıcı, 2026-09-28 — tasarım R3'ün ön-eleme için öncülü kodla ÇELİŞİYOR): `prescreen._sandbox`
`SKIP_COPY`'yi BİLEREK SORMAZ ve `meridian.db`(+`-wal`/`-shm`)'yi KOPYALAR. Ön-eleme kum havuzu iki defteri o
kopyadan okur (damga kopyada da dolu) — geçmiş zaten görünür. Orada maddeleştirme YAPILMAZ: DB-otoriter bir
varlığın yanına yazılan kanonik dosya bayat-defter süzgecine takılır (`.migrated-<ts>` + olay gürültüsü).
Karar yardımcıdadır: "kum havuzu DB taşıyorsa maddeleştirme yok".
"""
from __future__ import annotations

import json

import pytest

from meridian import config, dbmigrate, prescreen, sprint, storage, store, validation

HYP, VAL = "hypotheses.jsonl", "validation_ledger.jsonl"

HYP_SATIRLAR = [
    {"id": "H00001", "ts": "2026-08-01T10:00:00+00:00", "variable": "entry.min_score", "old": 60,
     "new": 62.5, "rationale": "r", "predicted_direction": "up", "predicted_delta": 0.01,
     "confidence": 0.6, "regime": "trend_up", "source": "reflect", "version_from": 4,
     "version_to": None, "status": "rejected_by_backtest", "market_regime": "trend_up"},
    {"id": "H00002", "ts": "2026-08-02T10:00:00+00:00", "variable": "exit.trail_r", "old": None,
     "new": 3, "rationale": "r", "predicted_direction": "down", "predicted_delta": -0.0,
     "confidence": 0.5, "regime": "chop", "source": "reflect", "version_from": 4,
     "version_to": 5, "status": "promoted", "market_regime": "chop"},
]
VAL_SATIRLAR = [
    {"ts": f"2026-08-0{i}T10:00:00+00:00", "fingerprint": "fp-r1", "etiket": f"k={i}",
     "degisen_params": {"k": i}, "eval_regime": None, "oos_score": 0.1 * i, "incumbent_oos": 0.2,
     "passes": i % 2 == 0, "gate_law": "para_v3", "fold_wins": "2/4", "tail_ok": True,
     "k_probes": i, "erosion_queries": 0, "n_trials": 10 + i, "oos_components": {"a": 1.0},
     "oos_ozet": {"n": 50}, "sharpe_gozlem": 0.5, "dsr": None, "varyans_kaynagi": "ledger",
     "seri": [["2026-01-02", 1.5 * i]], "beyan": "b", "pencere_id": "R1"}
    for i in range(1, 6)
]
TRADE = {"id": "T00001", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAPL",
         "side": "long", "r_multiple": 1.5, "strategy_version": 4}


@pytest.fixture
def canli(sandbox_state, monkeypatch):
    """Canlının göç SONRASI hâli: sekiz varlık DB'de, iki öğrenme defteri damgalı, kaynaklar `.migrated`."""
    monkeypatch.delenv("MERIDIAN_DB", raising=False)
    store._BAYAT_SUPURULDU.clear()
    yield sandbox_state
    storage.close_connections()
    store._BAYAT_SUPURULDU.clear()


def _yaz(state, ad, satirlar):
    (state / ad).write_text("".join(json.dumps(r) + "\n" for r in satirlar))


def _goc(state):
    _yaz(state, "trades.jsonl", [TRADE])
    _yaz(state, HYP, HYP_SATIRLAR)
    _yaz(state, VAL, VAL_SATIRLAR)
    r = dbmigrate.apply()
    assert r["ok"] is True and set(r["tasinan"]) >= {HYP, VAL}, r.get("hata")
    assert not (state / VAL).exists() and (state / (VAL + storage.MIGRATED_SUFFIX)).exists()
    assert store.db_backed(VAL) is True and len(store.read_jsonl(VAL)) == len(VAL_SATIRLAR)
    # WAL kontrol noktası (v45 deseni): kopya/okuma canlı defterin kendisini görsün
    storage.close_connections()


def _olaylar(state, event):
    p = state / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines()
            if x.strip() and json.loads(x).get("event") == event]


# ---- SPRINT: DB'SİZ KUM HAVUZU ------------------------------------------------------------------
def test_sprint_kum_havuzu_dbdeki_validation_gecmisini_gorur(canli, monkeypatch):
    _goc(canli)
    sbstate = sprint._kur_kum_havuzu("20990101-000001") / "state"
    assert not (sbstate / storage.DB_NAME).exists(), "izolasyon: kum havuzu DB'siz doğmalı"
    assert (sbstate / VAL).exists(), "canlı DB'deki validation geçmişi kum havuzuna inmedi (R3)"
    assert len((sbstate / VAL).read_text().splitlines()) == len(VAL_SATIRLAR)
    olay = _olaylar(canli, "sprint_kum_havuzu_maddelestirildi")
    assert len(olay) == 1
    assert {v["varlik"]: v["n"] for v in olay[0]["varliklar"]} == {
        HYP: len(HYP_SATIRLAR), VAL: len(VAL_SATIRLAR)}
    monkeypatch.setattr(config, "STATE", sbstate)          # artık ÇOCUĞUN gördüğü state
    assert store.db_backed(VAL) is False
    assert dbmigrate.digest(store.read_jsonl(VAL)) == dbmigrate.digest(VAL_SATIRLAR)
    assert [r["etiket"] for r in validation.ledger()] == [r["etiket"] for r in VAL_SATIRLAR]
    # sprint'in kendi sıfırlaması maddeleştirmenin ÜSTÜNE yazar (bugünkü davranış)
    assert store.read_jsonl(HYP) == []
    assert store.read_jsonl("trades.jsonl") == []


def test_sprint_canli_damgasizken_dosya_kopyasi_aynen_kalir(canli, monkeypatch):
    """Göç ÖNCESİ (D6-1 ile D6-2 arası): canlı defter dosyadan okunuyor → kopya zaten doğru; yazım YOK."""
    _yaz(canli, "trades.jsonl", [TRADE])
    assert dbmigrate.apply()["ok"] is True                  # yalnız trades taşınır, iki defter kaynak_yok
    _yaz(canli, VAL, VAL_SATIRLAR[:2])                      # canlıda dosyadan yaşayan defter
    storage.close_connections()
    assert store.db_backed(VAL) is False
    sbstate = sprint._kur_kum_havuzu("20990101-000002") / "state"
    assert _olaylar(canli, "sprint_kum_havuzu_maddelestirildi") == []
    assert (sbstate / VAL).read_text() == (canli / VAL).read_text()


# ---- ÖN-ELEME: DB KOPYALAYAN KUM HAVUZU ---------------------------------------------------------
def test_prescreen_kum_havuzu_db_kopyasindan_okur_maddelestirmez(canli, monkeypatch, tmp_path):
    _goc(canli)
    kayit: list[str] = []
    hedef = prescreen._sandbox(tmp_path / "work", config.STATE, log=kayit.append)
    assert (hedef / storage.DB_NAME).exists(), "ölçüm öncülü değişti: ön-eleme DB'yi artık kopyalamıyor"
    for ad in (HYP, VAL):
        assert not (hedef / ad).exists(), f"{ad}: DB-otoriter varlığın yanına kanonik dosya yazıldı"
    assert any("kum_havuzu_db_tasiyor" in s for s in kayit), kayit
    monkeypatch.setattr(config, "STATE", hedef)
    store._BAYAT_SUPURULDU.clear()
    assert store.db_backed(VAL) is True
    assert len(validation.ledger()) == len(VAL_SATIRLAR)
    assert _olaylar(hedef, "bayat_defter_arsivlendi") == []


# ---- YARDIMCI: KARAR TABLOSU ----------------------------------------------------------------------
def test_maddelestirme_karar_tablosu(canli, monkeypatch, tmp_path):
    kum = tmp_path / "kum"
    kum.mkdir()
    # (b) canlıda DB yok → canlı dosyadan okuyor: yazım yok
    sonuc = {r["varlik"]: r for r in store.kum_havuzuna_maddelestir(kum)}
    assert set(sonuc) == set(storage.DAMGA_KAPILI)
    assert all(r["durum"] == "canli_dosyadan" and r["n"] is None for r in sonuc.values())
    _goc(canli)
    # (c) damgalı + kum havuzu DB'siz → maddeleştirildi
    sonuc = {r["varlik"]: r for r in store.kum_havuzuna_maddelestir(kum, canli_state=canli)}
    assert sonuc[VAL] == {"varlik": VAL, "durum": "maddelestirildi", "n": len(VAL_SATIRLAR)}
    assert dbmigrate.digest([json.loads(x) for x in (kum / VAL).read_text().splitlines()]) \
        == dbmigrate.digest(VAL_SATIRLAR)
    # eski altıya UYGULANMAZ
    assert not (kum / "trades.jsonl").exists()
    # (a) kum havuzu DB taşıyor → yazım yok
    kum2 = tmp_path / "kum2"
    kum2.mkdir()
    (kum2 / storage.DB_NAME).write_bytes(b"")
    sonuc = store.kum_havuzuna_maddelestir(kum2)
    assert all(r["durum"] == "kum_havuzu_db_tasiyor" for r in sonuc) and not (kum2 / VAL).exists()
    # (e) canlı kök config.STATE DEĞİL → yanlış DB'den okunmaz
    kum3 = tmp_path / "kum3"
    kum3.mkdir()
    sonuc = store.kum_havuzuna_maddelestir(kum3, canli_state=tmp_path / "baska")
    assert all(r["durum"] == "canli_kok_config_disinda" for r in sonuc) and not (kum3 / VAL).exists()
    # (d) MERIDIAN_DB=off → canlı dosyadan okuyor sayılır
    monkeypatch.setenv("MERIDIAN_DB", "off")
    kum4 = tmp_path / "kum4"
    kum4.mkdir()
    sonuc = store.kum_havuzuna_maddelestir(kum4)
    assert all(r["durum"] == "canli_dosyadan" for r in sonuc) and not (kum4 / VAL).exists()

"""v580 — TSK-020 Kademe C D3: atomik oku-değiştir-yaz (`store.update_rows`) — R2 süreçler-arası kayıp güncelleme.

SPEC: `docs/TASARIM-SQLITE-KADEME-C-2026-09-28.md` D3 (operatör ONAYLI 2026-09-28).

R2 (ölçüldü, tasarım §3): `memory.update_status`/`writeback_outcome` defterin TAMAMINI okur, değiştirir, TAMAMINI
yeniden yazar; okuma yalnız süreç-içi `_HYP_LOCK` altındaydı. Aynı anda öğrenme süreci `memory.record` ile
KİLİTSİZ ekleme yapar → okuma ile yazma arasına düşen ekleme yeniden yazımda SİLİNİR. SQLite'a taşımak bunu
tek başına çözmez (`replace_rows` "hepsini sil + yaz", okuma transaction DIŞINDA).

ÇÖZÜM: DB yolunda oku→fn→yaz TEK `BEGIN IMMEDIATE` içinde — başka bir bağlantının eklemesi transaction'ı
BEKLER ve COMMIT'ten SONRA iner, kaybolmaz. Dosya yolunda okuma+yazmayı kapsayan dosya kilidi
(`store.update_jsonl`); eklemenin kilitsiz O_APPEND kararı DEĞİŞMEZ (`tests/test_wph_store_kapi.py`) — dosya
yolunda yarış yalnız DB'siz kiplerde kalır ve beyanla kabul edilir (tasarım D3).

ÇİVİ DESENİ (zamanlamasız, deterministik): araya giren yazar `busy_timeout=0` ile AYRI bir bağlantıdır.
Atomik yolda transaction açıkken eklemesi ANINDA `database is locked` alır → COMMIT'ten sonra yeniden dener
→ satır YAŞAR. Eski oku-sonra-yaz yolunda ekleme araya GİRER ve tam yeniden yazım onu SİLER.
"""
from __future__ import annotations

import fcntl
import json
import os
import sqlite3

import pytest

from meridian import dbmigrate, memory, obs, storage, store

HYP = memory.HYP

TABAN = [
    {"id": "H00001", "ts": "2026-08-01T10:00:00+00:00", "variable": "entry.min_score", "old": 60,
     "new": 62.5, "rationale": "r", "predicted_direction": "up", "predicted_delta": 0.01,
     "confidence": 0.6, "regime": "trend_up", "source": "reflect", "version_from": 4,
     "version_to": 5, "status": "live", "market_regime": "trend_up"},
    {"id": "H00002", "ts": "2026-08-02T10:00:00+00:00", "variable": "exit.trail_r", "old": 2.0,
     "new": 3, "rationale": "r", "predicted_direction": "down", "predicted_delta": -0.01,
     "confidence": 0.5, "regime": "chop", "source": "reflect", "version_from": 5,
     "version_to": None, "status": "proposed", "market_regime": "chop"},
]
ARAYA = {"id": "H00099", "ts": "2026-08-03T10:00:00+00:00", "variable": "yarisan.ekleme",
         "old": None, "new": 1, "rationale": "başka süreç", "predicted_direction": "up",
         "predicted_delta": 0.0, "confidence": 0.1, "regime": "any", "source": "learn",
         "version_from": 5, "version_to": None, "status": "proposed", "market_regime": "any"}


@pytest.fixture
def db_sandbox(sandbox_state, monkeypatch):
    monkeypatch.delenv("MERIDIAN_DB", raising=False)
    store._BAYAT_SUPURULDU.clear()
    yield sandbox_state
    storage.close_connections()
    store._BAYAT_SUPURULDU.clear()


def _gocmus_db(state):
    """Canlı D6-2 sonrası hâl: hipotez defteri DB'de, damgalı."""
    (state / HYP).write_text("".join(json.dumps(r) + "\n" for r in TABAN))
    r = dbmigrate.apply()
    assert r["ok"] is True and HYP in r["tasinan"], r.get("hata")
    assert store.db_backed(HYP) is True


class _YarisanYazar:
    """AYRI bağlantı = ayrı süreç (SQLite kilidi bağlantı başınadır). `busy_timeout=0`: kilit
    tutuluyorsa BEKLEMEZ, anında düşer — çivi zamanlamaya değil kilidin VARLIĞINA bakar."""

    def __init__(self, satir):
        self.satir = satir
        self.erken = None           # True: transaction açıkken ekleyebildi (= kilit YOKTU)
        self.con = sqlite3.connect(str(storage.db_path()), isolation_level=None, timeout=0)
        self.con.execute("PRAGMA busy_timeout=0")

    def _ekle(self):
        vals, extra = storage._row_to_cols(HYP, self.satir)
        cols = [c for c, _ in storage._COLS[HYP]]
        self.con.execute("BEGIN IMMEDIATE")
        try:
            self.con.execute(
                f'INSERT INTO hypotheses ({",".join(chr(34) + c + chr(34) for c in cols)},extra_json) '
                f'VALUES ({",".join("?" * (len(cols) + 1))})', (*vals, extra))
            self.con.execute("COMMIT")
        except BaseException:
            self.con.execute("ROLLBACK")
            raise

    def dene(self):
        """oku-değiştir-yaz'ın ORTASINDA çağrılır."""
        try:
            self._ekle()
            self.erken = True
        except sqlite3.OperationalError as e:
            assert "locked" in str(e), e
            self.erken = False

    def bitir(self):
        """Transaction bittikten sonra: erken ekleyemediyse şimdi ekler (gerçek yazarın busy_timeout'u)."""
        if self.erken is False:
            self._ekle()
        self.con.close()


def _idler():
    return [r["id"] for r in store.read_jsonl(HYP)]


# ---- DB YOLU: ARAYA GİREN EKLEME YAŞAR ------------------------------------------------------------
def test_update_rows_db_yolu_araya_giren_ekleme_yasar(db_sandbox):
    _gocmus_db(db_sandbox)
    yazar = _YarisanYazar(ARAYA)

    def fn(rows):
        yazar.dene()
        rows[1]["status"] = "rejected_by_gate"
        return True

    store.update_rows(HYP, fn)
    yazar.bitir()
    assert yazar.erken is False, "transaction açıkken başka bağlantı yazabildi — oku+yaz atomik DEĞİL"
    assert _idler() == ["H00001", "H00002", "H00099"], "araya giren ekleme SİLİNDİ (R2)"
    assert store.read_jsonl(HYP)[1]["status"] == "rejected_by_gate"


def test_update_status_db_yolunda_araya_giren_ekleme_yasar(db_sandbox, monkeypatch):
    """Üretim yolu: `memory.update_status` fn'in içinde `now_iso` çağırır (gerçek geçiş damgası) — araya
    giren yazar oraya bağlanır. Eski kod (tam oku → değiştir → tam yaz) eklemeyi silerdi."""
    _gocmus_db(db_sandbox)
    yazar = _YarisanYazar(ARAYA)
    gercek = memory.now_iso

    def _now(ts=None):
        if yazar.erken is None:
            yazar.dene()
        return gercek(ts)

    monkeypatch.setattr(memory, "now_iso", _now)
    out = memory.update_status("H00002", "rejected_by_gate", reason="test")
    yazar.bitir()
    assert out is not None and out["status"] == "rejected_by_gate"
    assert yazar.erken is False
    assert _idler() == ["H00001", "H00002", "H00099"]
    satir = store.read_jsonl(HYP)[1]
    assert satir["status"] == "rejected_by_gate" and satir["reason"] == "test" and satir["status_ts"]


def test_writeback_outcome_db_yolunda_araya_giren_ekleme_yasar(db_sandbox, monkeypatch):
    _gocmus_db(db_sandbox)
    yazar = _YarisanYazar(ARAYA)
    gercek = memory.now_iso

    def _now(ts=None):
        if yazar.erken is None:
            yazar.dene()
        return gercek(ts)

    monkeypatch.setattr(memory, "now_iso", _now)
    out = memory.writeback_outcome(5, 0.0123456, {"market_regime": "chop", "n": 9})
    yazar.bitir()
    assert out is not None and out["id"] == "H00001"
    assert yazar.erken is False
    assert _idler() == ["H00001", "H00002", "H00099"]
    h1 = store.read_jsonl(HYP)[0]
    assert h1["realized_delta"] == 0.0123 and h1["calibration_hit"] is True
    assert h1["market_regime"] == "chop" and h1["outcome_ts"]


# ---- DOSYA YOLU: OKUMA+YAZMA TEK KİLİT ALTINDA ------------------------------------------------------
def test_update_rows_dosya_yolu_okuma_yazma_ayni_kilidin_altinda(db_sandbox):
    """DB'siz kip (kum havuzu / `MERIDIAN_DB=off`): fn koşarken süreçler-arası flock TUTULUYOR olmalı."""
    (db_sandbox / HYP).write_text("".join(json.dumps(r) + "\n" for r in TABAN))
    assert store.db_backed(HYP) is False
    kilit = db_sandbox / ".locks" / (HYP + ".lock")
    tutuluyor = {}

    def fn(rows):
        fd = os.open(str(kilit), os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            tutuluyor["v"] = False
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            tutuluyor["v"] = True
        finally:
            os.close(fd)
        rows[0]["status"] = "promoted"
        return True

    store.update_rows(HYP, fn)
    assert tutuluyor.get("v") is True, "fn koşarken dosya kilidi tutulmuyordu"
    assert store.read_jsonl(HYP)[0]["status"] == "promoted"


# ---- İŞ MANTIĞI İKİ ARKA UÇTA AYNEN ---------------------------------------------------------------
@pytest.fixture(params=["dosya", "db"])
def arka_uc(request, db_sandbox):
    (db_sandbox / HYP).write_text("".join(json.dumps(r) + "\n" for r in TABAN))
    if request.param == "db":
        assert dbmigrate.apply()["ok"] is True
    assert store.db_backed(HYP) is (request.param == "db")
    return request.param


def _rev():
    return storage.meta(HYP)["rev"] if store.db_backed(HYP) else store.stamp(HYP)


def test_terminal_durumdan_donus_reddedilir_ve_yazilmaz(arka_uc):
    memory.update_status("H00001", "promoted")
    once = _rev()
    assert memory.update_status("H00001", "proposed") is None
    assert _rev() == once, "reddedilen geçiş deftere YAZDI"
    assert store.read_jsonl(HYP)[0]["status"] == "promoted"
    olay = [r for r in obs.recent(50) if r.get("event") == "illegal_status_transition"]
    assert olay and olay[-1]["hyp_id"] == "H00001"


def test_status_ts_yalniz_gercek_geciste_damgalanir(arka_uc, monkeypatch):
    monkeypatch.setattr(memory, "now_iso", lambda ts=None: "2026-09-01T00:00:00+00:00")
    memory.update_status("H00002", "live")
    assert store.read_jsonl(HYP)[1]["status_ts"] == "2026-09-01T00:00:00+00:00"
    monkeypatch.setattr(memory, "now_iso", lambda ts=None: "2026-09-02T00:00:00+00:00")
    memory.update_status("H00002", "live", note="tazeleme")
    satir = store.read_jsonl(HYP)[1]
    assert satir["status_ts"] == "2026-09-01T00:00:00+00:00" and satir["note"] == "tazeleme"


def test_bilinmeyen_kimlik_none_ve_yazim_yok(arka_uc):
    once = _rev()
    assert memory.update_status("H99999", "live") is None
    assert memory.writeback_outcome(99, 0.1, {}) is None
    assert _rev() == once


def test_promoted_sonucu_tek_yonlu_kilitli(arka_uc):
    memory.update_status("H00001", "promoted")
    ilk = memory.writeback_outcome(5, 0.02, {"n": 1})
    assert ilk["realized_delta"] == 0.02
    once = _rev()
    ikinci = memory.writeback_outcome(5, -0.5, {"n": 2})
    assert ikinci["realized_delta"] == 0.02 and _rev() == once
    assert store.read_jsonl(HYP)[0]["realized_delta"] == 0.02


def test_numpy_degeri_sanitize_edilir(arka_uc):
    np = pytest.importorskip("numpy")
    out = memory.writeback_outcome(5, float(np.float64(0.01)), {"ic": np.float64(0.5), "n": np.int64(3)})
    assert out is not None
    satir = store.read_jsonl(HYP)[0]
    assert satir["realized_detail"] == {"ic": 0.5, "n": 3}
    assert type(satir["realized_detail"]["n"]) is int

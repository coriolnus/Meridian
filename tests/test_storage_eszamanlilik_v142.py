"""test_storage_eszamanlilik_v142.py — İKİ SÜREÇ, AYNI DEFTER (WP-H/H9, Kademe B2/B3 kanıtı).

NEDEN BU TEST VAR. Bu depodaki `file_lock` bir `threading.RLock`ti, yani YALNIZ aynı süreçte
anlam taşıyordu; `update_scoreboard` ise HİÇ kilit almıyordu. Canlı worker, pano API'si ve elle
tetiklenen ölçüm yolları AYNI dosyalara yazıyor. Kayıp güncelleme burada hiçbir istisna fırlatmaz:
karne satırı sessizce eski hâline döner, defter satırı sessizce kaybolur — yani bu depodaki baskın
kusur sınıfının ta kendisi.

TEK KANIT BİÇİMİ: İKİ AYRI SÜREÇ. Süreç-içi iplikler `RLock`u zaten paylaşıyordu; eski kodun
kırıldığı yer tam olarak SÜREÇ SINIRIYDI. `multiprocessing` (spawn) iki bağımsız yorumlayıcı
başlatır — biri diğerinin kilit sözlüğünü göremez. Testin geçmesi flock'un (dosya arka ucu) ve
WAL + busy_timeout'un (SQLite arka ucu) GERÇEKTEN devrede olduğunu söyler.

İKİ ARKA UÇ DA ÖLÇÜLÜR: geçiş sırasında ikisi de canlıdır (kod dağıtımı ile veri migrasyonu ayrı
iki olaydır) ve "yalnız SQLite'ta güvenli" bir kilit, geçiş penceresinde kilit olmamasıdır.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os

import pytest

from meridian import config, dbmigrate, storage, store

N_YAZIM = 40          # süreç başına oku-değiştir-yaz turu
ETIKETLER = (1, 2)


def _isci(kok: str, etiket: int, n: int, kuyruk) -> None:
    """AYRI SÜREÇTE koşar: karneye oku-değiştir-yaz + deftere ekleme."""
    os.environ["MERIDIAN_ROOT"] = kok
    from meridian import store as _store, versioning as _ver
    hata = None
    try:
        for i in range(n):
            _ver.update_scoreboard(etiket * 1000 + i, live_score=float(i), yazan=etiket)
            _store.append_jsonl("trades.jsonl",
                                {"id": f"T{etiket}-{i:03d}", "ticker": "AAA", "side": "long",
                                 "ts_open": "2026-01-02", "ts_close": "2026-01-09",
                                 "entry": 10.0, "exit": 11.0, "qty": 1, "r_multiple": 1.0,
                                 "pnl_dollars": 1.0, "plan_id": f"P-2026-01-02-A{etiket}{i}",
                                 "regime": "chop", "score": 60, "setup": "breakout_vcp",
                                 "strategy_version": 4, "yazan": etiket})
    except Exception as e:                      # noqa: BLE001 — çocuk sürecin hatası KANITTIR
        hata = f"{type(e).__name__}: {e}"
    kuyruk.put((etiket, hata))


def _kosur(kok: str) -> list[tuple[int, str | None]]:
    ctx = mp.get_context("spawn")
    kuyruk = ctx.Queue()
    isciler = [ctx.Process(target=_isci, args=(kok, e, N_YAZIM, kuyruk), daemon=False)
               for e in ETIKETLER]
    for p in isciler:
        p.start()
    sonuc = [kuyruk.get(timeout=180) for _ in isciler]
    for p in isciler:
        p.join(timeout=60)
        assert p.exitcode == 0, f"çocuk süreç {p.pid} çıkış kodu {p.exitcode}"
    return sonuc


def _dogrula(sonuc) -> None:
    for etiket, hata in sonuc:
        assert hata is None, f"süreç {etiket} düştü: {hata}"

    # (1) KARNE: iki sürecin yazdığı HER satır durmalı. Kilitsiz oku-değiştir-yazda geç kalan
    #     yazar, arada yazılmış satırları eski kopyasıyla geri alır — kayıp burada görünür.
    sb = store.read_json("scoreboard.json", {"versions": {}})
    beklenen = {str(e * 1000 + i) for e in ETIKETLER for i in range(N_YAZIM)}
    eksik = beklenen - set(sb.get("versions", {}))
    assert not eksik, (f"KAYIP GÜNCELLEME: karnede {len(eksik)} satır yok "
                       f"(örnek: {sorted(eksik)[:8]}) — oku-değiştir-yaz kilidi süreç sınırını "
                       f"geçmiyor")
    assert isinstance(sb.get("current_version"), int)

    # (2) DEFTER: her ekleme durmalı ve satırlar BOZULMAMIŞ olmalı.
    rows = store.read_jsonl("trades.jsonl")
    ids = [r.get("id") for r in rows]
    assert len(ids) == len(set(ids)) == len(ETIKETLER) * N_YAZIM, \
        f"kayıp/çift satır: {len(ids)} satır, {len(set(ids))} benzersiz kimlik"
    for e in ETIKETLER:
        assert sum(1 for r in rows if r.get("yazan") == e) == N_YAZIM
    # Alan bütünlüğü: yarım yazılmış bir satır tipli alanları kaybederdi.
    assert all(isinstance(r.get("entry"), float) and isinstance(r.get("score"), int)
               and r.get("setup") == "breakout_vcp" for r in rows)


@pytest.fixture
def kok(tmp_path, monkeypatch):
    """Sandbox kök + çocuk süreçlerin göreceği MERIDIAN_ROOT. `sandbox_state` KULLANILMAZ:
    çocuk süreç ana sürecin monkeypatch'ini göremez, yalnız ORTAM DEĞİŞKENİNİ görür — yani iki
    tarafın aynı dizine bakmasının tek dürüst yolu budur."""
    state = tmp_path / "state"
    (state / "history").mkdir(parents=True)
    monkeypatch.setenv("MERIDIAN_ROOT", str(tmp_path))
    monkeypatch.setattr(config, "STATE", state)
    monkeypatch.setattr(config, "HISTORY", state / "history")
    yield tmp_path
    storage.close_all()


def test_iki_surec_dosya_arka_ucunda_yazim_kaybetmez(kok):
    """DOSYA arka ucu: `fcntl.flock` kanıtı (eski `threading.RLock` burada kaybederdi)."""
    (config.STATE / "trades.jsonl").write_text("")
    (config.STATE / "scoreboard.json").write_text(json.dumps({"current_version": None,
                                                              "versions": {}}))
    _dogrula(_kosur(str(kok)))
    assert not storage.db_path().exists(), "dosya arka ucu testinde DB doğmamalı"
    # Dosya GERÇEKTEN geçerli JSON/JSONL kalmalı (yarım yazım sınıfı)
    json.loads((config.STATE / "scoreboard.json").read_text())
    with open(config.STATE / "trades.jsonl") as f:
        assert all(json.loads(line) for line in f if line.strip())


def test_iki_surec_sqlite_arka_ucunda_yazim_kaybetmez(kok):
    """SQLite arka ucu: WAL + busy_timeout + tek-transaction kanıtı."""
    (config.STATE / "trades.jsonl").write_text("")
    (config.STATE / "scoreboard.json").write_text(json.dumps({"current_version": None,
                                                              "versions": {}}))
    rapor = dbmigrate.apply()
    assert rapor["ok"] is True and store.db_backed("trades.jsonl") is True
    _dogrula(_kosur(str(kok)))
    # Bütünlük çekirdeğin kendi ölçümüyle de doğrulanır — "bozulma yok" iddiası bizim değil.
    c = storage.connect()
    assert c.execute("PRAGMA integrity_check").fetchone()["integrity_check"] == "ok"
    assert storage.pragma_state()["journal_mode"] == "wal"

"""test_storage_v142.py — SQLite defter çekirdeği (WP-H/H9, Kademe A).

NE ÖLÇER: PRAGMA'lar İDDİA DEĞİL ÖLÇÜM mü, parite digesti gerçekten bir kapı mı (bozulunca
migrasyon DÜŞÜYOR mu), migrasyon idempotent mi, kaynak dosyalar SİLİNİYOR mu (silinmemeli),
tekil belge yazımı atomik mi, ve DB devreye girdiğinde `store` çağıranlarının aldığı yapı
DEĞİŞMİYOR mu (dış imza sözleşmesi).
"""
from __future__ import annotations

import json

import pytest

from meridian import config, dbmigrate, storage, store, versioning


@pytest.fixture
def db_sandbox(sandbox_state):
    """Sandbox + bağlantı temizliği. Bağlantılar süreç ömrü boyunca havuzda kalır; her test kendi
    tmp yoluna açar, ama tanıtıcıları bırakmak uzun suite'te fd sızdırır."""
    yield sandbox_state
    storage.close_connections()


TRADE = {"id": "T00001", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAPL",
         "side": "long", "entry": 100.5, "exit": 110.25, "qty": 10, "r_multiple": 1.5,
         "pnl_pct": 0.097, "pnl_dollars": 97.5, "costs": 1.2, "exit_reason": "target",
         "strategy_version": 4, "regime": "trend_up", "setup": "breakout_vcp", "score": 72,
         "r_multiple_expected": 2.5, "exploration": False, "plan_id": "P-2026-01-02-AAPL",
         "skill_chain": ["vcp-screener"], "bars_held": 5, "scaled_out": False,
         "mfe_r": 1.9, "mae_r": 0.4}
PLAN = {"id": "P-2026-01-02-AAPL", "date": "2026-01-02", "ticker": "AAPL", "side": "long",
        "entry_trigger": 100.0, "stop": 95.0, "profit_target": 112.5, "targets": [112.5],
        "size_r": 1.0, "r_multiple_expected": 2.5, "regime_at_plan": "trend_up",
        "strategy_version": 4, "skill_chain": ["vcp-screener"], "sector": "Technology",
        "score": 72, "setup": "breakout_vcp", "gate_verdict": "GO", "gate_reasons": [],
        "gate_checks": [{"name": "rs", "ok": True}]}
BOOK = {"cash": 94457.91, "realized_pnl": -5542.09, "last_id": 95, "positions": {},
        "armed": [], "pending_exits": {}, "last_date": "2026-07-28",
        "day_start_equity": 94457.91, "peak_equity": 102520.45}
SB = {"current_version": 3, "versions": {"3": {"live_score": -0.0089, "n_trades": 95}}}
EQ = {"version": 4, "points": [["2026-01-02", 100000.0], ["2026-01-09", 100097.5]]}


def _seed_files(state):
    (state / "trades.jsonl").write_text(json.dumps(TRADE) + "\n")
    (state / "trade_plans.jsonl").write_text(json.dumps(PLAN) + "\n")
    (state / "portfolio.json").write_text(json.dumps(BOOK, indent=2))
    (state / "scoreboard.json").write_text(json.dumps(SB, indent=2))
    (state / "equity_curve.json").write_text(json.dumps(EQ, indent=2))


# ---- 1. PRAGMA'LAR ÖLÇÜLÜR ---------------------------------------------------------------------
def test_pragmalar_iddia_degil_olcum(db_sandbox):
    """WAL/NORMAL/busy_timeout/foreign_keys AÇIK bağlantıda GERÇEKTEN geçerli mi?

    Neden test: `PRAGMA journal_mode=WAL` KALICIDIR (dosyaya yazılır) ama `synchronous`,
    `busy_timeout` ve `foreign_keys` BAĞLANTI ÖMÜRLÜdür — bağlantı fabrikası onları her açılışta
    basmazsa ikinci süreç sessizce varsayılanlarla koşar ve "WAL + busy_timeout var" cümlesi
    ölçülmemiş bir iddiaya döner."""
    storage.ensure_schema()          # DB'yi yaratma yetkisi olan TEK yol
    p = storage.pragma_state()
    assert p["journal_mode"] == "wal"
    assert p["synchronous"] == 1          # NORMAL
    assert p["busy_timeout"] == 5000
    assert p["foreign_keys"] == 1
    assert storage.schema_version() == storage.SCHEMA_VERSION == 1


def test_db_yolu_cagri_aninda_cozulur(db_sandbox, tmp_path, monkeypatch):
    """Yol modül YÜKLEME anında dondurulursa ölçüm sandbox'ları kırılır (bu depoda belgeli sınıf)."""
    assert storage.db_path().parent == config.STATE
    baska = tmp_path / "baska_state"
    baska.mkdir()
    monkeypatch.setattr(config, "STATE", baska)
    assert storage.db_path().parent == baska


# ---- 2. PARİTE DİGESTİ BİR KAPIDIR --------------------------------------------------------------
def test_migrasyon_parite_digestini_dogrular(db_sandbox):
    _seed_files(db_sandbox)
    rapor = dbmigrate.apply()
    assert rapor["ok"] is True and rapor["yazildi"] is True
    esles = {p["varlik"]: p for p in rapor["parite"]}
    for ad in ("trades.jsonl", "trade_plans.jsonl", "scoreboard.json",
               "portfolio.json", "equity_curve.json"):
        assert esles[ad]["durum"] == "tasindi", esles[ad]
        assert esles[ad]["kaynak_digest"] == esles[ad]["db_digest"]
    # shadow_books.json yok → uydurulmuş bir belge YAZILMAZ
    assert esles["shadow_books.json"]["durum"] == "kaynak_yok"
    assert store.read_json("shadow_books.json", None) is None


def test_parite_tutmazsa_migrasyon_duser_ve_geri_alinir(db_sandbox):
    """Digest bir SÜS değil KAPIdır: eşleşmezse hiçbir varlık taşınmaz.

    Kanıt üretimi: DB'den okumayı bozarız (tek satır düşürülür). Parite turu bunu görmeli,
    transaction geri alınmalı ve DB'de HİÇBİR satır kalmamalı.

    YAMA `monkeypatch` FİKSTÜRÜNE BAĞLANMAZ (bu depoda üç kez yazılı ders): `monkeypatch.undo()`
    O FİKSTÜRÜN TÜM yamalarını söker — `sandbox_state`in `config.STATE` yamasını da. Test o an
    farkında olmadan CANLI `state/` dizinine bakmaya başlar; ilk yazımda canlı defteri kirletirdi.
    Kendi yamasını kendi kurar, `try/finally` ile kendi söker."""
    _seed_files(db_sandbox)
    gercek = storage.read_entity

    def _bozuk(name):
        out = gercek(name)
        return out[:-1] if name == "trades.jsonl" and isinstance(out, list) else out

    storage.read_entity = _bozuk
    try:
        rapor = dbmigrate.apply()
    finally:
        storage.read_entity = gercek
    assert rapor["ok"] is False
    assert "PARİTE TUTMADI" in rapor["hata"]
    # GERİ ALMA GERÇEK — ama SORU DEĞİŞTİ (C4, 2026-08-02). Burada eskiden
    # `storage.read_entity(...) == []` soruluyordu: HAM DB katmanına sorulan bir soru, ve dönen []
    # "tamamı geri alındı" diye okunuyordu. Aynı anda `store.read_jsonl` DA [] dönüyordu, çünkü
    # geride ŞEMALI-BOŞ ama `active()`in True dediği bir DB kalıyordu — altı defter sessizce boş
    # okunuyordu ve bu test onu görmüyordu. Başarısız migrasyon artık geride AKTİF DB BIRAKMAZ,
    # dolayısıyla doğru soru "UYGULAMA ne okuyor?"tur. (Çiviler: test_denetim_defter_v159.py)
    assert storage.active(storage.TRADES) is False and not storage.db_path().exists()
    assert store.read_jsonl("trades.jsonl") == [TRADE]        # defter dosyadan GERÇEK okunuyor
    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]
    assert (db_sandbox / "trades.jsonl").exists()
    assert not (db_sandbox / "trades.jsonl.migrated").exists()


def test_bozuk_kaynak_sessizce_atlanmaz(db_sandbox):
    """Okunamayan bir kaynak "dosya yok" ile AYNI şey değildir — sessizce atlanırsa defter kaybolur."""
    _seed_files(db_sandbox)
    (db_sandbox / "portfolio.json").write_text("{ bozuk json")
    rapor = dbmigrate.apply()
    assert rapor["ok"] is False and "portfolio.json" in rapor["hata"]
    # (C4, 2026-08-02) — gerekçe için bkz. `test_parite_tutmazsa_...`: soru HAM DB katmanına değil,
    # uygulamanın okuduğu katmana sorulur. Başarısız migrasyondan sonra DB DEVREDE DEĞİLDİR.
    assert storage.active(storage.TRADES) is False
    assert store.read_jsonl("trades.jsonl") == [TRADE]    # defter KAYBOLMADI (eskiden [] dönerdi)


# ---- 3. İDEMPOTENS + ARŞİVLEME -----------------------------------------------------------------
def test_iki_kez_uygula_ayni_sonuc(db_sandbox):
    _seed_files(db_sandbox)
    r1 = dbmigrate.apply()
    d1 = {x["varlik"]: x["db_digest"] for x in r1["db_durumu"]}
    r2 = dbmigrate.apply()
    d2 = {x["varlik"]: x["db_digest"] for x in r2["db_durumu"]}
    assert r2["ok"] is True
    assert r2["yazildi"] is False              # ikinci koşu hiçbir şey taşımaz
    assert d1 == d2
    assert all(p["durum"] in ("zaten_tasindi", "kaynak_yok") for p in r2["parite"])
    assert len(store.read_jsonl("trades.jsonl")) == 1        # satır İKİYE katlanmadı


def test_durum_raporu_kaynak_digestini_TASIR(db_sandbox):
    """Migrasyonun KANITI DB'de kalmalı: `entity_meta.source_digest`, taşınan verinin kaynak
    parmak izidir ve `--durum` onu okur. İlk sürümde `storage.meta` sütunları ELLE sayıyordu ve
    bu sütun listede yoktu — rapor sessizce `null` basıyordu, yani migrasyonun kendi kanıtı
    kaybolmuştu (elle yazılan sütun listesi eskir sınıfı)."""
    _seed_files(db_sandbox)
    dbmigrate.apply()
    durum = {r["varlik"]: r for r in dbmigrate.db_state()}
    for ad in ("trades.jsonl", "trade_plans.jsonl", "scoreboard.json",
               "portfolio.json", "equity_curve.json"):
        assert durum[ad]["kaynak_digest"], f"{ad}: kaynak digesti kaydedilmemiş"
        assert durum[ad]["kaynak_digest"] == durum[ad]["db_digest"], ad
        assert durum[ad]["migrated_at"]


def test_kaynak_dosyalar_silinmez_migrated_ekiyle_durur(db_sandbox):
    _seed_files(db_sandbox)
    dbmigrate.apply()
    for ad in ("trades.jsonl", "trade_plans.jsonl", "scoreboard.json",
               "portfolio.json", "equity_curve.json"):
        assert not (db_sandbox / ad).exists(), f"{ad} yerinde kaldı — iki gerçek kaynak olur"
        arsiv = db_sandbox / (ad + ".migrated")
        assert arsiv.exists() and arsiv.stat().st_size > 0
    # Arşiv İÇERİĞİ hâlâ okunabilir olmalı: `MERIDIAN_DB=off` geri dönüşünün anlamı budur.
    assert json.loads((db_sandbox / "portfolio.json.migrated").read_text())["cash"] == BOOK["cash"]


# ---- 4. DIŞ İMZA SÖZLEŞMESİ (çağıranlar aynı yapıyı alır) --------------------------------------
def test_store_cagiranlari_ayni_yapiyi_alir(db_sandbox):
    _seed_files(db_sandbox)
    once = {"trades": store.read_jsonl("trades.jsonl"),
            "plans": store.read_jsonl("trade_plans.jsonl"),
            "pf": store.read_json("portfolio.json", {}),
            "sb": store.read_json("scoreboard.json", {}),
            "eq": store.read_json("equity_curve.json", {"points": []})}
    dbmigrate.apply()
    assert store.db_backed("trades.jsonl") is True
    sonra = {"trades": store.read_jsonl("trades.jsonl"),
             "plans": store.read_jsonl("trade_plans.jsonl"),
             "pf": store.read_json("portfolio.json", {}),
             "sb": store.read_json("scoreboard.json", {}),
             "eq": store.read_json("equity_curve.json", {"points": []})}
    for k in once:
        assert dbmigrate.digest(once[k]) == dbmigrate.digest(sonra[k]), k
    # TİP KORUNUR: SQLite afinitesi int'i float'a çevirseydi digest zaten tutmazdı, ama tek tek
    # de söylenir — bu, migrasyonun en sessiz kaybetme yoluydu.
    t = store.read_jsonl("trades.jsonl")[0]
    assert isinstance(t["score"], int) and isinstance(t["entry"], float)
    assert t["exploration"] is False and isinstance(t["skill_chain"], list)


def test_limit_son_satirlari_verir(db_sandbox):
    _seed_files(db_sandbox)
    dbmigrate.apply()
    for i in range(2, 6):
        store.append_jsonl("trades.jsonl", dict(TRADE, id=f"T0000{i}"))
    assert [r["id"] for r in store.read_jsonl("trades.jsonl", limit=2)] == ["T00004", "T00005"]
    assert len(store.read_jsonl("trades.jsonl")) == 5


def test_env_kapatma_anahtari_dosyaya_dondurur(db_sandbox, monkeypatch):
    """`MERIDIAN_DB=off` acil geri dönüş: DB dursa bile dosya yolu geçerli olmalı."""
    _seed_files(db_sandbox)
    dbmigrate.apply()
    assert store.db_backed("trades.jsonl") is True
    monkeypatch.setenv("MERIDIAN_DB", "off")
    assert store.db_backed("trades.jsonl") is False
    assert store.read_jsonl("trades.jsonl") == []       # dosya .migrated oldu — DÜRÜST boşluk


# ---- 5. TEKİL BELGE ATOMİKLİĞİ ------------------------------------------------------------------
def test_tekil_belge_yazimi_atomik_ve_geri_alinabilir(db_sandbox):
    """Yarım belge YOKTUR: transaction düşerse ÖNCEKİ belge aynen durur."""
    _seed_files(db_sandbox)
    dbmigrate.apply()
    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]
    c = storage.connect()
    c.execute("BEGIN IMMEDIATE")
    storage.do_write_doc(c, "portfolio.json", {"cash": 1.0, "positions": {}})
    c.execute("ROLLBACK")
    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]
    # Başarılı yazım ise TAM görünür (ara hâl yok)
    store.write_json("portfolio.json", {**BOOK, "cash": 12345.0})
    assert store.read_json("portfolio.json", {})["cash"] == 12345.0
    assert store.read_json("portfolio.json", {})["last_id"] == 95


def test_karne_kilitli_yoldan_gecer_ve_satir_kaybetmez(db_sandbox):
    """`update_scoreboard`/`set_row_fields` eskiden kilitsiz oku-değiştir-yazdı (B3)."""
    _seed_files(db_sandbox)
    dbmigrate.apply()
    versioning.update_scoreboard(5, live_score=0.4)
    versioning.set_row_fields(3, note="ölçüm")
    sb = store.read_json("scoreboard.json", {})
    assert sb["current_version"] == 5                     # ship yolu canlı sürümü taşır
    assert sb["versions"]["5"]["live_score"] == 0.4
    assert sb["versions"]["3"]["note"] == "ölçüm"
    assert sb["versions"]["3"]["n_trades"] == 95          # eski alanlar EZİLMEDİ


# ---- 6. TAZELİK DAMGASI ARKA UÇTAN BAĞIMSIZ ----------------------------------------------------
def test_damga_icerik_degisince_degisir(db_sandbox):
    """`.migrated` dosyanın mtime'ı DONDUĞU için damga DB'den okunmalı; yoksa her önbellek
    sonsuza kadar bayat kalırdı (analytics/_nd_stamp, shadow_model, intraday_cycle, watchdog)."""
    _seed_files(db_sandbox)
    dosya_damga = store.stamp("trades.jsonl")
    assert dosya_damga != (0, 0)
    dbmigrate.apply()
    d1 = store.stamp("trades.jsonl")
    store.append_jsonl("trades.jsonl", dict(TRADE, id="T00002"))
    d2 = store.stamp("trades.jsonl")
    assert d1 != d2, "içerik değişti ama damga aynı kaldı — önbellek sonsuza kadar bayat kalırdı"
    assert store.mtime("trades.jsonl") is not None
    assert store.mtime("shadow_books.json") is None       # hiç yazılmamış varlık: ölçüm YOK


# ---- 7. YEDEK TUTARLI OLMALI --------------------------------------------------------------------
def test_yedek_tutarli_kopya_uretir(db_sandbox, tmp_path):
    """WAL modunda ham dosya kopyası EKSİK olur; yedek çevrimiçi yedek API'sinden geçmeli.
    (`/api/state/snapshot` ve gece rsync'i bu yolu kullanır — eksik bir yedek, geri yükleme
    gününe kadar görünmez.)"""
    _seed_files(db_sandbox)
    dbmigrate.apply()
    store.append_jsonl("trades.jsonl", dict(TRADE, id="T00002"))   # WAL'da bekleyen yazım
    hedef = storage.backup_to(tmp_path / "yedek" / "meridian.db")
    import sqlite3
    c = sqlite3.connect(str(hedef))
    c.row_factory = storage._dict_row
    assert c.execute("PRAGMA integrity_check").fetchone()["integrity_check"] == "ok"
    assert c.execute("SELECT COUNT(*) AS n FROM trades").fetchone()["n"] == 2
    assert c.execute("SELECT COUNT(*) AS n FROM trade_plans").fetchone()["n"] == 1
    c.close()

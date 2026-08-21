"""test_bayat_defter_kalintisi_v234.py — bayat-defter-kalıntısı tuzağı (ROADMAP Ö-6).

NE ÖLÇER (VLO adli incelemesi bulgusunun kapanışı, 2026-08-11): defterler DB'ye göçtükten sonra
kanonik adda kalan/yeniden doğan DÜZ dosyalar insan+araç tarafından bayat okunuyordu (canlıda
trades.jsonl 95 satırda donuk; DB 97). Üç çivi:

  1. GÖÇ-LİSTESİ ↔ .migrated DİSİPLİNİ EŞLİĞİ: `storage.ENTITIES`e giren HER varlık, migrasyonda
     kanonik adını kaybedip `.migrated` arşivi kazanır — liste üzerinden ölçülür ki yarın eklenen
     yedinci varlık bu sözleşmeye kendiliğinden bağlansın (elle yazılmış ad listesi eskir sınıfı).
  2. SÜZGEÇ: göç-edilmiş varlığın kanonik dosyası SONRADAN duruyorsa/doğarsa, DB'nin devrede
     olduğu ilk `store.db_backed` temasında `.migrated` disiplinine çekilir (hedef doluysa
     zaman-damgalı ad — hiçbir şey silinmez/ezilmez), olay basılır; `migrated_at` damgasız dosya
     TAŞINMAZ, yalnız beyan edilir (ona `.migrated` demek uydurma olurdu).
  3. OKUMA YOLU DB-OTORİTER — SÜZGEÇTEN BAĞIMSIZ: kanonik adda ayrışık bir dosya DURSA BİLE
     `store.read_json/read_jsonl` dosyaya DÜŞMEZ; süzgeç bastırılmışken bile DB okunur.
"""
from __future__ import annotations

import json
import os

import pytest

from meridian import dbmigrate, storage, store


@pytest.fixture
def db_sandbox(sandbox_state):
    """Sandbox + bağlantı temizliği + süzgeç damgasının sıfırlanması. Damga süreç-ömürlüdür ve
    yol-anahtarlıdır; sandbox yolları benzersiz olsa da testler damgayı BİLEREK kurcalar
    (bastırma/yeniden-tetikleme) — iki yönde de temiz başlamak, testleri sıraya duyarsız kılar."""
    store._BAYAT_SUPURULDU.clear()
    yield sandbox_state
    storage.close_connections()
    store._BAYAT_SUPURULDU.clear()


TRADE = {"id": "T00001", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAPL",
         "side": "long", "entry": 100.5, "exit": 110.25, "qty": 10, "r_multiple": 1.5,
         "score": 72, "exploration": False, "strategy_version": 4}
PLAN = {"id": "P-2026-01-02-AAPL", "date": "2026-01-02", "ticker": "AAPL", "side": "long",
        "entry_trigger": 100.0, "stop": 95.0, "score": 72}
BOOK = {"cash": 94457.91, "last_id": 95, "positions": {}}
SB = {"current_version": 3, "versions": {"3": {"n_trades": 95}}}
EQ = {"version": 4, "points": [["2026-01-02", 100000.0]]}
SHB = {"variants": {"v9": {"n": 3}}}

_DOC = {"trades.jsonl": TRADE, "trade_plans.jsonl": PLAN, "scoreboard.json": SB,
        "portfolio.json": BOOK, "equity_curve.json": EQ, "shadow_books.json": SHB}


def _seed(state, adlar=None):
    """Varlıkları TÜRÜNE göre diskten tohumla — ad listesi `storage.ENTITIES`ten türetilir."""
    for ad in (adlar if adlar is not None else storage.ENTITIES):
        icerik = _DOC[ad]
        if storage.kind_of(ad) == "rows":
            (state / ad).write_text(json.dumps(icerik) + "\n")
        else:
            (state / ad).write_text(json.dumps(icerik, indent=2))


def _olaylar(event):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == event]


# ---- 1. GÖÇ-LİSTESİ ↔ .migrated DİSİPLİNİ EŞLİĞİ ----------------------------------------------
def test_goc_listesine_giren_HER_varlik_migrated_disiplinine_baglanir(db_sandbox):
    """Elle ad listesi değil `storage.ENTITIES` üzerinden: kaynağı olan her varlık taşınır,
    kanonik adı düşer, `.migrated` arşivi doğar. Yarın eklenen varlık bu testten kaçamaz."""
    _seed(db_sandbox)
    rapor = dbmigrate.apply()
    assert rapor["ok"] is True and rapor["yazildi"] is True
    assert set(rapor["tasinan"]) == set(storage.ENTITIES)
    assert sorted(rapor["arsivlenen"]) == sorted(ad + storage.MIGRATED_SUFFIX
                                                 for ad in storage.ENTITIES)
    for ad in storage.ENTITIES:
        assert not (db_sandbox / ad).exists(), f"{ad} kanonik adda kaldı — iki gerçek kaynak olur"
        arsiv = db_sandbox / (ad + storage.MIGRATED_SUFFIX)
        assert arsiv.exists() and arsiv.stat().st_size > 0, ad
    # Süzgeç bu temiz tabloda HİÇBİR şey yapmaz (yanlış-pozitif çivisi).
    store._BAYAT_SUPURULDU.clear()
    assert store.db_backed("trades.jsonl") is True      # tetik
    assert _olaylar("bayat_defter_arsivlendi") == []
    assert _olaylar("db_aktif_kanonik_dosya_gocsuz") == []


# ---- 2. SÜZGEÇ: kalıntı ilk temasta arşive çekilir ---------------------------------------------
def test_kalinti_dosya_ilk_temasta_migrated_olur_ve_adli_sinyaller_olculur(db_sandbox):
    """Canlı 95-satır vakasının birebir simülasyonu: arşiv yok + kanonik dosya migrasyon
    kaynağının donuk kopyası. Süzgeç dosyayı TAM `.migrated` adına çeker; olay, adli sinyalleri
    (boyut, dosya mtime'ı, migrasyonun kaynak digesti) rename'den ÖNCEKİ ölçümle taşır."""
    _seed(db_sandbox)
    kaynak_satiri = (db_sandbox / "trades.jsonl").read_text()
    dbmigrate.apply()
    arsiv = db_sandbox / ("trades.jsonl" + storage.MIGRATED_SUFFIX)
    arsiv.rename(db_sandbox / "trades.jsonl.kenara")        # canlıda arşivin hiç doğmadığı hâl
    (db_sandbox / "trades.jsonl").write_text(kaynak_satiri)  # kalıntı = migrasyon kaynağı
    store._BAYAT_SUPURULDU.clear()

    assert [r["id"] for r in store.read_jsonl("trades.jsonl")] == ["T00001"]   # DB'den, dosyadan değil
    assert not (db_sandbox / "trades.jsonl").exists(), "kalıntı kanonik adda kaldı"
    assert arsiv.exists() and arsiv.read_text() == kaynak_satiri
    olay = _olaylar("bayat_defter_arsivlendi")
    assert len(olay) == 1 and olay[0].get("hatalar") is None
    kayit = {k["dosya"]: k for k in olay[0]["arsivlenen"]}
    assert kayit["trades.jsonl"]["hedef"] == "trades.jsonl" + storage.MIGRATED_SUFFIX
    assert kayit["trades.jsonl"]["boyut"] == len(kaynak_satiri.encode())
    assert kayit["trades.jsonl"]["dosya_mtime"] is not None
    assert kayit["trades.jsonl"]["kaynak_digest"] == storage.meta("trades.jsonl")["source_digest"]


def test_kalinti_arsiv_doluyken_ezilmez_zaman_damgali_ada_gider(db_sandbox):
    """`dbmigrate.apply` arşiv döngüsünün sessiz atladığı (a) sınıfı: hedef `.migrated` DOLU.
    POSIX rename dolu hedefi sessizce ezerdi — süzgeç ezmek yerine zaman-damgalı ada taşır;
    kalıntının boyutu/mtime'ı olaydan okunur (arşivle karşılaştırma operatörün elinde kalır)."""
    _seed(db_sandbox)
    dbmigrate.apply()
    arsiv = db_sandbox / ("trades.jsonl" + storage.MIGRATED_SUFFIX)
    arsiv_icerik = arsiv.read_text()
    bayat = json.dumps(dict(TRADE, id="T-BAYAT")) + "\n"
    (db_sandbox / "trades.jsonl").write_text(bayat)          # göç sonrası ayrışık kalıntı
    store._BAYAT_SUPURULDU.clear()

    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]       # tetik (başka addan)
    assert not (db_sandbox / "trades.jsonl").exists()
    assert arsiv.read_text() == arsiv_icerik, "dolu arşiv EZİLDİ — veri kaybı"
    damgali = [p.name for p in db_sandbox.iterdir()
               if p.name.startswith("trades.jsonl" + storage.MIGRATED_SUFFIX + "-")]
    assert len(damgali) == 1 and f"-p{os.getpid()}" in damgali[0]
    assert (db_sandbox / damgali[0]).read_text() == bayat
    kayit = {k["dosya"]: k for k in _olaylar("bayat_defter_arsivlendi")[0]["arsivlenen"]}
    assert kayit["trades.jsonl"]["hedef"] == damgali[0]
    assert kayit["trades.jsonl"]["boyut"] == len(bayat.encode())


def test_gocsuz_kanonik_dosya_tasinmaz_yalniz_beyan_edilir(db_sandbox):
    """`migrated_at` damgası olmayan varlığın dosyasına `.migrated` demek UYDURMA olurdu:
    içeriğinin DB'ye geçtiği kanıtlanmadı. Dosya YERİNDE kalır, olayla beyan edilir; okuyucu yine
    DB-otoriterdir (varlık DB'de yok → çağıranın varsayılanı, dosya OKUNMAZ)."""
    _seed(db_sandbox, [ad for ad in storage.ENTITIES if ad != "shadow_books.json"])
    dbmigrate.apply()                                        # shadow_books: kaynak_yok → damgasız
    (db_sandbox / "shadow_books.json").write_text(json.dumps(SHB))   # off-penceresi doğumu simüle
    store._BAYAT_SUPURULDU.clear()

    assert store.read_json("shadow_books.json", None) is None        # dosya DEĞİL, DB (yok) okundu
    assert (db_sandbox / "shadow_books.json").exists(), "damgasız dosya taşındı — uydurma arşiv"
    assert not (db_sandbox / ("shadow_books.json" + storage.MIGRATED_SUFFIX)).exists()
    olay = _olaylar("db_aktif_kanonik_dosya_gocsuz")
    assert len(olay) == 1 and olay[0]["dosyalar"] == ["shadow_books.json"]
    assert _olaylar("bayat_defter_arsivlendi") == []


def test_suzgec_db_kapaliyken_yapisal_olarak_devre_disi(db_sandbox, monkeypatch):
    """`MERIDIAN_DB=off` iken dosyalar OTORİTERDİR — süzgeç kanonik dosyaya dokunursa defteri
    yok eder. `db_backed` False döndüğü için süzgeç hiç tetiklenmez (yapısal kapı)."""
    _seed(db_sandbox)
    dbmigrate.apply()
    kalinti = json.dumps(dict(TRADE, id="T-OFF")) + "\n"
    (db_sandbox / "trades.jsonl").write_text(kalinti)
    store._BAYAT_SUPURULDU.clear()
    monkeypatch.setenv("MERIDIAN_DB", "off")

    assert store.db_backed("trades.jsonl") is False
    store.read_jsonl("trades.jsonl")
    assert (db_sandbox / "trades.jsonl").read_text() == kalinti, "off modunda kanonik dosya taşındı"


def test_suzgec_surec_basina_bir_kez_ve_idempotent(db_sandbox):
    """Damga işten öncedir (obs→append_jsonl→db_backed özyineleme kapısı) ve ikinci koşu —
    zorla tetiklense bile — temiz tabloda YENİ olay üretmez."""
    _seed(db_sandbox)
    dbmigrate.apply()
    (db_sandbox / "trades.jsonl").write_text(json.dumps(TRADE) + "\n")
    store._BAYAT_SUPURULDU.clear()
    store.read_jsonl("trades.jsonl")                         # 1. tetik: kalıntıyı arşivler
    n1 = len(_olaylar("bayat_defter_arsivlendi"))
    assert n1 == 1
    store.read_jsonl("trades.jsonl")                         # damga: süzgeç bir daha koşmaz
    store._BAYAT_SUPURULDU.clear()
    store.read_jsonl("trades.jsonl")                         # zorla ikinci koşu: kalıntı yok
    assert len(_olaylar("bayat_defter_arsivlendi")) == n1, "idempotens kırıldı — olay seli"


# ---- 3. OKUMA YOLU DB-OTORİTER — SÜZGEÇTEN BAĞIMSIZ ÇİVİ ---------------------------------------
def test_okuma_yolu_dosyaya_dusmez_suzgec_bastirilmisken_bile(db_sandbox):
    """Çivi iki fazlıdır. FAZ 1 — süzgeç BASTIRILMIŞ: kanonik adda ayrışık dosya dururken
    read_json/read_jsonl DB'yi döndürür ve dosyaya DOKUNMAZ (otorite okuyucunun kendisinde,
    süzgece bağımlı değil). FAZ 2 — süzgeç serbest: aynı okuma kalıntıyı arşive çeker."""
    _seed(db_sandbox)
    dbmigrate.apply()
    (db_sandbox / "portfolio.json").write_text(json.dumps({"cash": -999999.0, "last_id": 1}))
    (db_sandbox / "trades.jsonl").write_text(json.dumps(dict(TRADE, id="T-SAHTE")) + "\n")
    store._BAYAT_SUPURULDU.clear()
    store._BAYAT_SUPURULDU.add(str(storage.db_path()))       # FAZ 1: süzgeç bastırıldı

    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]
    assert [r["id"] for r in store.read_jsonl("trades.jsonl")] == ["T00001"]
    store.write_json("portfolio.json", {**BOOK, "cash": 777.0})      # yazım da DB'ye gider
    assert store.read_json("portfolio.json", {})["cash"] == 777.0
    assert json.loads((db_sandbox / "portfolio.json").read_text())["cash"] == -999999.0, \
        "okuma/yazma yolu kanonik DOSYAYA dokundu — DB-otoriterlik delik"
    assert store.stamp("portfolio.json") != (0, 0) and store.mtime("portfolio.json") is not None

    store._BAYAT_SUPURULDU.clear()                           # FAZ 2: süzgeç serbest
    assert store.read_json("portfolio.json", {})["cash"] == 777.0
    assert not (db_sandbox / "portfolio.json").exists()
    assert not (db_sandbox / "trades.jsonl").exists()

"""test_kovab_yapi_v163.py — DENETİM 2026-08-02, KOVA-B (YAPI) kümesi.

İKİ BULGUYU ÇİVİLER:

  C3 (run.py + Dockerfile + docker-compose.yml + README.md) — `run.worker()` 24/7 kadansın İKİNCİ
     bir uygulamasıydı, ÜRETİMDE HİÇ KOŞMUYORDU ve tam da bu yüzden zamanlayıcıda adıyla
     düzeltilmiş üç kusuru (seans tanımı · `load_live` veri yolu · koşulsuz ilerleme) son gününe
     kadar taşıyordu. Çivilenen invariant: TEK KADANS. `worker()` artık kadans koşmaz, yüksek
     sesle yönlendirir; başlatma dosyalarının hiçbiri `python -m meridian.run`ı 24/7 yol diye
     göstermez.

  C5 (dbmigrate.py + storage.py) — `MERIDIAN_DB=off` "acil geri dönüş anahtarı" diye belgelenmişti
     ama tek başına defterleri BOŞ okutuyordu (kaynaklar `.migrated` adında; kanonik ad yok →
     çağıranın varsayılanı) ve geri-alma kolu HİÇ yoktu. Çivilenen invariant: GERİ DÖNÜŞ BİR
     KOLDUR (`dbmigrate --geri-al`) ve VERİ SİLMEZ — DB kenara alınır, arşivler asıl adlarına
     döner, ayrışık kitap ezilmez, fark raporlanır; anahtarın yarım hâli SESSİZ kalmaz.

CANLI STATE'E YAZILMAZ: her test `sandbox_state` (tmp_path + `config.STATE` monkeypatch) içinde
koşar; son testte canlı yolun dokunulmadığı ayrıca ölçülür.
"""
from __future__ import annotations

import inspect
import json
import pathlib

import pytest

from meridian import config, dbmigrate, run, storage, store

REPO = pathlib.Path(__file__).resolve().parent.parent


# ==================================================================================================
# C5 — GERİ ALMA KOLU (`dbmigrate --geri-al`)
# ==================================================================================================
TRADE_A = {"id": "T00001", "ticker": "AAPL", "side": "long", "entry": 100.5, "qty": 10,
           "strategy_version": 4, "regime": "trend_up", "score": 72}
TRADE_B = {"id": "T00002", "ticker": "MSFT", "side": "long", "entry": 310.0, "qty": 3,
           "strategy_version": 4, "regime": "trend_up", "score": 65}
BOOK = {"cash": 94457.91, "realized_pnl": -5542.09, "last_id": 42,
        "positions": {"AAPL": {"qty": 10}}, "armed": [], "last_date": "2026-08-01"}
SB = {"current_version": 3, "versions": {"3": {"live_score": -0.0089, "n_trades": 2}}}


@pytest.fixture
def db_sandbox(sandbox_state, monkeypatch):
    """Sandbox + `MERIDIAN_DB` KESİN olarak temiz (kabuk ortamı testi yönlendiremesin)."""
    monkeypatch.delenv("MERIDIAN_DB", raising=False)
    storage.close_connections()
    yield sandbox_state
    storage.close_connections()


def _seed(state) -> None:
    (state / "trades.jsonl").write_text(json.dumps(TRADE_A) + "\n" + json.dumps(TRADE_B) + "\n")
    (state / "portfolio.json").write_text(json.dumps(BOOK))
    (state / "scoreboard.json").write_text(json.dumps(SB))


def _yan_dbler(state, ek: str) -> list[str]:
    return sorted(p.name for p in state.iterdir() if p.name.startswith(storage.DB_NAME + ek))


def _olaylar(state, event: str) -> list[dict]:
    p = state / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines()
            if x.strip() and json.loads(x).get("event") == event]


def test_c5_geri_al_tam_tur(db_sandbox):
    """UYGULA → GERİ AL: dosyalar ASIL adlarında, DB kenarda, `active()` False, defterler DOSYADAN.

    Kusurun tam karşıtı: eskiden bu tur ancak elle `mv` ile tamamlanabiliyordu ve o adım hiçbir
    yerde yazılı değildi — `MERIDIAN_DB=off` çeken operatör altı defteri boş okuyordu."""
    _seed(db_sandbox)
    assert dbmigrate.apply()["ok"] is True
    assert store.db_backed("trades.jsonl") is True, "kurulum tutmadı: DB devreye girmedi"

    rapor = dbmigrate.rollback()

    assert rapor["ok"] is True and rapor["yapildi"] is True
    # 1) DB DEVREDE DEĞİL ve kanonik adda DEĞİL — ama SİLİNMEDİ
    assert rapor["aktif"] is False and storage.active(storage.TRADES) is False
    assert store.db_backed("trades.jsonl") is False
    assert not storage.db_path().exists()
    assert len(_yan_dbler(db_sandbox, dbmigrate.ROLLEDBACK_SUFFIX)) == 1
    assert rapor["db_kenara"]["yapildi"] is True and rapor["db_kenara"]["hedef"]
    # 2) ARŞİVLER ASIL ADINA DÖNDÜ — `.migrated` geride kalmadı
    for ad in ("trades.jsonl", "portfolio.json", "scoreboard.json"):
        assert (db_sandbox / ad).exists(), ad
        assert not (db_sandbox / (ad + dbmigrate.MIGRATED_SUFFIX)).exists(), ad
        assert ad in rapor["geri_donen"], ad
    # 3) DEFTERLER DOSYADAN OKUNUYOR — "geri döndüm" cümlesi ölçümle doğrulanır
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]
    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]
    assert store.read_json("scoreboard.json", {}) == SB
    # 4) Hiçbir yazım YOKKEN parite tam: DB ne okuduysa dosya da onu taşır
    esles = {v["varlik"]: v for v in rapor["varliklar"]}
    assert esles["trades.jsonl"]["fark"] == 0 and esles["trades.jsonl"]["digest_esit"] is True
    assert rapor["fark_var"] == []
    # 5) Karar OLAY DEFTERİNE geçti
    assert len(_olaylar(db_sandbox, "sqlite_ledger_rolled_back")) == 1


def test_c5_geri_al_idempotent(db_sandbox):
    """İKİNCİ ÇAĞRI ZARAR VERMEZ ve BEYANLA döner — kurtarma kolu tereddütle iki kez çekilir."""
    _seed(db_sandbox)
    dbmigrate.apply()
    dbmigrate.rollback()
    once = {ad: (db_sandbox / ad).read_text()
            for ad in ("trades.jsonl", "portfolio.json", "scoreboard.json")}
    kenar_once = _yan_dbler(db_sandbox, dbmigrate.ROLLEDBACK_SUFFIX)

    rapor = dbmigrate.rollback()

    assert rapor["ok"] is True and rapor["yapildi"] is False
    assert rapor["geri_donen"] == [] and rapor["db_kenara"]["yapildi"] is False
    assert "GERİ ALINACAK BİR ŞEY YOK" in rapor["beyan"]
    # HİÇBİR DOSYA DEĞİŞMEDİ — ikinci çağrı ne ezer ne ikinci bir kopya doğurur
    for ad, icerik in once.items():
        assert (db_sandbox / ad).read_text() == icerik, ad
    assert _yan_dbler(db_sandbox, dbmigrate.ROLLEDBACK_SUFFIX) == kenar_once
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]


def test_c5_geri_al_parite_farkini_raporlar_ve_DB_YI_SILMEZ(db_sandbox):
    """MİGRASYON SONRASI YAZIMLAR ARŞİVDE YOKTUR. Kol o satırları geri getiremez — ama sessiz
    kalamaz: fark rapora çıkar ve tek kopyalarını taşıyan DB dosyası SİLİNMEZ."""
    _seed(db_sandbox)
    dbmigrate.apply()
    store.append_jsonl("trades.jsonl", {"id": "T00003", "ticker": "NVDA", "entry": 500.0})
    assert len(store.read_jsonl("trades.jsonl")) == 3

    rapor = dbmigrate.rollback()

    fark = {f["varlik"]: f for f in rapor["fark_var"]}
    assert fark["trades.jsonl"]["db_n"] == 3 and fark["trades.jsonl"]["dosya_n"] == 2
    assert fark["trades.jsonl"]["fark"] == 1 and fark["trades.jsonl"]["digest_esit"] is False
    assert "SİLME" in rapor["beyan"] and "DİKKAT" in rapor["beyan"]
    # Kenara alınan DB GERÇEKTEN duruyor ve T00003 hâlâ İÇİNDE (veri silinmedi, taşındı)
    kenar = db_sandbox / _yan_dbler(db_sandbox, dbmigrate.ROLLEDBACK_SUFFIX)[0]
    import sqlite3
    c = sqlite3.connect(str(kenar))
    try:
        idler = [r[0] for r in c.execute("SELECT id FROM trades ORDER BY seq").fetchall()]
    finally:
        c.close()
    assert idler == ["T00001", "T00002", "T00003"], "kenara alınan DB'de satır kaybı"
    # Dosya arka ucu migrasyon ÖNCESİ hâli taşır — bu bir kayıp değil, BEYAN EDİLMİŞ bir fark
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]


def test_c5_geri_al_ayrisik_kitabi_EZMEZ(db_sandbox):
    """C5'in ikinci yüzü: `MERIDIAN_DB=off` çekiliyken yapılan ilk yazım AYRIŞIK bir kitap doğurur.
    Geri-al kanonik adı geri isterken o dosyayı silemez — kenara alır ve rapora yazar."""
    _seed(db_sandbox)
    dbmigrate.apply()
    # anahtar çekiliyken doğmuş ayrışık kitap (last_id sıfırlanmış, tek satır)
    (db_sandbox / "trades.jsonl").write_text(json.dumps({"id": "T00001", "ticker": "ZZZ"}) + "\n")

    rapor = dbmigrate.rollback()

    rec = {v["varlik"]: v for v in rapor["varliklar"]}["trades.jsonl"]
    assert rec["geri_donen"] is True and rec["ayrisik_kenara"], rec
    ayr = db_sandbox / rec["ayrisik_kenara"]
    assert ayr.exists() and json.loads(ayr.read_text().splitlines()[0])["ticker"] == "ZZZ"
    # kanonik ad ARŞİVİN içeriğini taşır
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]
    assert not (db_sandbox / ("trades.jsonl" + dbmigrate.MIGRATED_SUFFIX)).exists()


def test_c5_geri_al_wal_ve_shm_dosyalarini_da_tasir(db_sandbox, monkeypatch):
    """Ana dosya kenara alınıp `meridian.db-wal` kanonik adında kalsaydı, İLERİDE doğacak taze bir
    `meridian.db` BAYAT bir WAL'la eşleşirdi (C4 karantinasıyla aynı gerekçe, aynı yasa).

    ÖLÇÜM DÜRÜSTLÜĞÜ: yan dosyalar ELLE sahnelenir ve `db_state` bu testte devre dışı bırakılır.
    Sebep ölçüldü — `db_state()` DB'yi yeniden AÇAR, ardından `rollback`ün `close_connections()`
    çağrısı SQLite'a checkpoint attırır ve gerçek `-wal`/`-shm` dosyalarını SİLER; yani yeniden
    adlandırma döngüsüne hiç dosya kalmaz ve test kendi ölçtüğü şeye kör olurdu. Burada sınanan
    şey ölçüm adımı değil, ADLANDIRMA döngüsünün üç eki birden kapsamasıdır."""
    _seed(db_sandbox)
    dbmigrate.apply()
    storage.close_connections()
    monkeypatch.setattr(dbmigrate, "db_state", lambda: [])
    for ek in ("-wal", "-shm"):
        (db_sandbox / (storage.DB_NAME + ek)).write_bytes(b"x")

    rapor = dbmigrate.rollback()

    kalanlar = [p.name for p in db_sandbox.iterdir()
                if p.name.startswith(storage.DB_NAME)
                and dbmigrate.ROLLEDBACK_SUFFIX not in p.name]
    assert kalanlar == [], f"kanonik DB adıyla dosya kaldı: {kalanlar}"
    kenar = _yan_dbler(db_sandbox, dbmigrate.ROLLEDBACK_SUFFIX)
    assert len(kenar) == 3, kenar
    for ek in ("-wal", "-shm"):
        assert any(n.endswith(ek) for n in kenar), ek
    assert len(rapor["db_kenara"]["tasinan"]) == 3


def test_c5_geri_al_worker_KOSARKEN_reddedilir(db_sandbox, monkeypatch):
    """`--uygula` ile AYNI kapı: geri-al da arka ucu ayağın altından çeker. Ret, tek bayt
    değiştirmeden gerçekleşmeli."""
    _seed(db_sandbox)
    dbmigrate.apply()
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: True)

    kod = dbmigrate.main(["--geri-al"])

    assert kod == 2
    assert storage.db_path().exists(), "reddedilen koşu DB'yi yine de taşımış"
    assert (db_sandbox / ("trades.jsonl" + dbmigrate.MIGRATED_SUFFIX)).exists()
    assert not (db_sandbox / "trades.jsonl").exists()
    assert _yan_dbler(db_sandbox, dbmigrate.ROLLEDBACK_SUFFIX) == []
    # `--zorla` kapıyı açar (riski operatör alır)
    assert dbmigrate.main(["--geri-al", "--zorla"]) == 0
    assert (db_sandbox / "trades.jsonl").exists()


def test_c5_uygula_ile_geri_al_ayni_kosuda_reddedilir(db_sandbox, monkeypatch):
    """ÇELİŞKİLİ NİYET SESSİZCE SIRALANMAZ: sonucun hangi bayrağa ait olduğu raporda görünmezdi."""
    _seed(db_sandbox)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: True)   # kapıya hiç gelinmemeli
    assert dbmigrate.main(["--uygula", "--geri-al"]) == 2
    assert not storage.db_path().exists(), "çelişkili çağrı yine de taşımış"


def test_c5_db_off_kaynaklar_arsivdeyken_BEYANLI_uyarir(db_sandbox, monkeypatch):
    """Bulgunun 'defterleri boşaltıyor' yarısı: anahtar çekiliyken defterler boş okunuyor. Boş
    okuma ENGELLENMEZ (okuma kapısında istisna, panoyu ve worker'ı topyekûn düşürürdü) — ama
    SESSİZ de kalamaz."""
    _seed(db_sandbox)
    dbmigrate.apply()
    monkeypatch.setenv("MERIDIAN_DB", "off")
    storage.close_connections()

    # ölçülen hâl: defterler gerçekten boş okunuyor (bu, iddia değil ÖLÇÜM)
    assert store.read_jsonl("trades.jsonl") == []
    assert store.read_json("portfolio.json", None) is None

    uyari = _olaylar(db_sandbox, "db_off_kaynaklar_arsivde")
    assert len(uyari) == 1, f"beyan yok ya da tekrarlıyor: {len(uyari)}"
    assert set(uyari[0]["arsivde"]) == {"trades.jsonl", "portfolio.json", "scoreboard.json"}
    assert "--geri-al" in uyari[0]["detail"], "uyarı kolun adını söylemiyor"

    # SÜREÇ BAŞINA BİR KEZ: sonraki okumalar olay defterini sele çevirmez
    for _ in range(5):
        store.read_jsonl("trades.jsonl")
        store.read_json("scoreboard.json", {})
    assert len(_olaylar(db_sandbox, "db_off_kaynaklar_arsivde")) == 1


def test_c5_db_off_uyarisi_YANLIS_YERDE_yanmaz(db_sandbox, monkeypatch):
    """Uyarı YALNIZ yarım-geri-dönüş hâlini anlatır. İki karşı-durumda susmalı, yoksa jeton
    anlamını yitirir: (a) migrasyon hiç olmamışsa (DB yok), (b) geri-al çekilmişse (arşiv yok)."""
    _seed(db_sandbox)
    monkeypatch.setenv("MERIDIAN_DB", "off")
    storage.close_connections()
    assert len(store.read_jsonl("trades.jsonl")) == 2        # (a) DB yok → dosya zaten okunuyor
    assert _olaylar(db_sandbox, "db_off_kaynaklar_arsivde") == []

    monkeypatch.delenv("MERIDIAN_DB")
    storage.close_connections()
    dbmigrate.apply()
    dbmigrate.rollback()                                      # (b) kol çekildi: arşiv kalmadı
    monkeypatch.setenv("MERIDIAN_DB", "off")
    storage.close_connections()
    assert len(store.read_jsonl("trades.jsonl")) == 2
    assert _olaylar(db_sandbox, "db_off_kaynaklar_arsivde") == []


def test_c5_arsiv_eki_TEK_KAYNAKTAN_gelir(db_sandbox):
    """`storage` uyarısı ile `dbmigrate` arşivi AYNI eke bakmak zorunda: iki sabit olsaydı biri
    değiştiğinde uyarı arşivleri sessizce göremez olurdu (kusurun doğduğu sınıf)."""
    assert dbmigrate.MIGRATED_SUFFIX is storage.MIGRATED_SUFFIX


# ==================================================================================================
# C3 — İKİ KADANS YASASI TEK DEPODA YAŞAYAMAZ
# ==================================================================================================
def test_c3_worker_kadans_KOSMAZ_yonlendirir(sandbox_state, monkeypatch):
    """Emekliliğin BİÇİMİ: sessiz `return` değil, yüksek sesli `SystemExit(2)`. Kadans yolundaki
    her adım (veri yükleme, günlük döngü) çağrılsaydı test patlardı — çağrılmadıkları ölçülüyor."""
    from meridian import dataset, loop

    def _patlat(*a, **kw):
        raise AssertionError("EMEKLİ worker kadans koştu")

    monkeypatch.setattr(dataset, "load", _patlat)
    monkeypatch.setattr(loop, "daily_cycle", _patlat)

    with pytest.raises(SystemExit) as ex:
        run.worker(poll_seconds=1)
    assert ex.value.code == 2

    olay = _olaylar(sandbox_state, "retired_worker_invoked")
    assert len(olay) == 1 and "uvicorn" in olay[0]["detail"], olay
    assert olay[0]["poll_seconds"] == 1, "reddedilen çağrının niyeti kayda geçmedi"


def test_c3_ciplak_calistirma_worker_a_duser_ve_REDDEDER(sandbox_state, monkeypatch):
    """`python -m meridian.run` (bayraksız) = eski Dockerfile CMD'i. Sessizce çıkmamalı:
    `restart: unless-stopped` altında sessiz çıkış, hiçbir kadans koşmadan sağlıklı görünen bir
    yeniden başlatma döngüsüdür."""
    from meridian import dataset, loop
    monkeypatch.setattr(dataset, "load", lambda *a, **kw: pytest.fail("kadans koştu"))
    monkeypatch.setattr(loop, "daily_cycle", lambda *a, **kw: pytest.fail("kadans koştu"))

    with pytest.raises(SystemExit) as ex:
        run.main([])
    assert ex.value.code == 2
    # ESKİ bayrak hâlâ ayrıştırılır (eski bir betik "bilinmeyen argüman" ile düşmesin)
    with pytest.raises(SystemExit):
        run.main(["--poll", "30"])


def test_c3_worker_govdesinde_KADANS_KALMADI():
    """Kaynak düzeyinde çivi: gövdeye ne bir poll döngüsü ne takvim okuması ne `daily_cycle`
    dönebilir. Üç kusur da tam bu üç satırda yaşıyordu."""
    src = inspect.getsource(run.worker)
    for yasak in ("while True", "daily_cycle", "dataset.load", "mcal", "time.sleep",
                  "write_heartbeat"):
        assert yasak not in src, f"emekli worker hâlâ kadans taşıyor: {yasak}"
    assert "SystemExit" in src and "KADANS_YOLU" in src
    # modül artık takvim/uyku bağımlılığı taşımıyor (ikinci kadansın tek tüketicisiydi)
    kaynak = (REPO / "meridian" / "run.py").read_text()
    assert "pandas_market_calendars" not in kaynak
    assert "import time" not in kaynak


def test_c3_modul_docstringi_KALICI_KURALI_ve_geri_alinabilirligi_tasir():
    """YASA 6 (okuyucusuz yazım yok) tersinden: emekliliği okuyan kişi NEDENİNİ ve geri dönüş
    yolunu aynı yerde bulmalı, yoksa altıncı ayda dördüncü bir kadans doğar."""
    doc = run.__doc__ or ""
    assert "İki kadans yasası tek depoda yaşayamaz" in doc.replace("\n", " ")
    assert "GERİ ALINABİLİRLİK" in doc and "git show" in doc
    for kusur in ("sessions[-1]", "load_live", "last_processed"):
        assert kusur in doc, f"emekli edilen kusur beyan edilmemiş: {kusur}"


def test_c3_baslatma_dosyalari_ZAMANLAYICI_yolunda():
    """Bulgunun asıl gövdesi kod değil KOMUTTU: Dockerfile/compose/README `python -m meridian.run`ı
    24/7 yol diye gösteriyordu. Üçü de canlı A1 birimiyle (uvicorn + AUTOSTART_CYCLE) aynı yolu
    anlatmalı — `deploy/oracle-a1/meridian.service` bu turda DEĞİŞMEDİ, referanstır."""
    dockerfile = (REPO / "Dockerfile").read_text()
    compose = (REPO / "docker-compose.yml").read_text()
    readme = (REPO / "README.md").read_text()
    servis = (REPO / "deploy" / "oracle-a1" / "meridian.service").read_text()

    # YORUMLAR SAYILMAZ, KOMUTLAR SAYILIR: her iki dosya da emekliliğin GEREKÇESİNİ anlatırken
    # `meridian.run` adını anar. Ölçülen şey ÇALIŞTIRILAN satırdır.
    def _komut_satirlari(metin: str) -> list[str]:
        return [s for s in metin.splitlines() if s.strip() and not s.strip().startswith("#")]

    assert 'CMD ["uvicorn", "meridian.api:app"' in dockerfile
    assert all("meridian.run" not in s for s in _komut_satirlari(dockerfile)), "Dockerfile hâlâ koşuyor"
    # compose'un worker'ı kadansı SÜREÇ-İÇİ açar; komut artık ikinci bir uygulama değil
    assert all("meridian.run" not in s for s in _komut_satirlari(compose)), "compose hâlâ koşuyor"
    assert 'MERIDIAN_AUTOSTART_CYCLE: "1"' in compose
    assert compose.count("uvicorn") >= 2, "her iki servis de api sürecini koşmalı"
    # canlı birim referans: aynı iki bileşen orada da var (kopya değil, HİZA ölçümü)
    assert "MERIDIAN_AUTOSTART_CYCLE=1" in servis and "uvicorn meridian.api:app" in servis
    # README: çıplak `meridian.run` çağrısı 24/7 yol olarak ÖNERİLMİYOR
    ciplak = [s.strip() for s in readme.splitlines()
              if s.strip() in ("uv run python -m meridian.run", "python -m meridian.run")]
    assert ciplak == [], f"README hâlâ çıplak worker öneriyor: {ciplak}"
    assert "MERIDIAN_AUTOSTART_CYCLE=1" in readme


# ==================================================================================================
# DÜRÜSTLÜK KAPISI
# ==================================================================================================
def test_canli_state_dokunulmadi():
    """Bu dosyanın hiçbir testi canlı `state/`e yazmaz. `config.STATE` sandbox'a yamalıyken
    `db_path()` her çağrıda oradan türer — BURADA yama YOKTUR, yani okunan yol CANLI yoldur ve
    yalnız kenar dosyaların YOKLUĞU sorulur (DB açılmaz, yaratılmaz)."""
    assert storage.db_path() == config.STATE / storage.DB_NAME
    kirli = [p.name for p in config.STATE.iterdir() if p.is_file()
             and (dbmigrate.ROLLEDBACK_SUFFIX in p.name or dbmigrate.DIVERGENT_SUFFIX in p.name
                  or dbmigrate.FAILED_SUFFIX in p.name)]
    assert kirli == [], f"canlı state'te kurtarma artığı var — bir test sandbox dışına yazmış: {kirli}"

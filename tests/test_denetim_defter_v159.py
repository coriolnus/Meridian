"""test_denetim_defter_v159.py — DENETİM 2026-08-02, ÖĞRENME-KADANSI + DEFTER kümesi.

İKİ BULGUYU ÇİVİLER:

  C15 (sprint_run.py + sprint.py) — sprint kadans DAMGASI (`n_hyp_at_start`, `cfg`) çocuk sürecin
      ilk durum yazımında siliniyordu. Ölçülmüş sonucu: `should_run` tabanı 0 sayıyor,
      `taze = len(hyps) − 0` her zaman eşiği aşıyor ve `gun < 7` olsa bile "taze_aday_birikimi"
      tetikleniyordu — haftalık disiplin yerine HER GECE sprint. Çivilenen invariant:
      ÇOCUK YAZIMINDAN SONRA DA DAMGA OKUNABİLİR ve kadans tabanı sıfırlanmaz.

  C4 (dbmigrate.py + storage.py) — `ensure_schema` migrasyon transaction'ından ÖNCE kendi COMMIT'ini
      atıyordu; migrasyon KAYNAK_BOZUK/PARİTE_TUTMADI/istisna ile dönünce geride ŞEMALI-BOŞ ama
      `active()`in True dediği bir DB kalıyor, altı defter SESSİZCE boş okunuyordu. Çivilenen
      invariant: BAŞARISIZ MİGRASYONDAN SONRA DB DEVREDE DEĞİLDİR — `store` dosya arka ucundan
      GERÇEK satırları okur, kaynak dosyalar dokunulmamıştır, ve başarılı yol regresyonsuzdur.

CANLI STATE'E YAZILMAZ: her test `sandbox_state` (tmp_path + `config.STATE` monkeypatch) içinde
koşar; `MERIDIAN_SPRINT_STATUS` de sandbox'taki dosyayı gösterir.
"""
from __future__ import annotations

import datetime as dt
import json

import pytest

from meridian import config, dbmigrate, sprint, sprint_run, storage, store


# ==================================================================================================
# C15 — SPRINT KADANS DAMGASI
# ==================================================================================================
@pytest.fixture
def sprint_sandbox(sandbox_state, monkeypatch):
    """Sandbox + çocuk sürecin gördüğü `MERIDIAN_SPRINT_STATUS` yolu (CANLI dosya DEĞİL)."""
    monkeypatch.setenv("MERIDIAN_SPRINT_STATUS", str(sandbox_state / sprint.STATUS_FILE))
    return sandbox_state


PARENT_STAMP = {"pid": 999999, "sid": "20260802-000000", "phase": "starting",
                "started_at": "2026-08-02T00:11:00+00:00",
                "cfg": {"k_max": 3, "budget": 12}, "sbroot": "/tmp/sb/20260802-000000",
                "eval_start": sprint.EVAL_START, "cutoff": sprint.CUTOFF,
                "n_hyp_at_start": 41}


def _child_payload(**kw) -> dict:
    """`sprint_run._run`in `status()` fonksiyonunun ÜRETTİĞİ sabit payload — birebir aynı anahtarlar
    (damga alanları burada YOKTUR; kusurun tamamı bu eksiklikti)."""
    return {"pid": 999999, "sid": PARENT_STAMP["sid"], "started_at": PARENT_STAMP["started_at"],
            "sbroot": PARENT_STAMP["sbroot"], "eval_start": sprint.EVAL_START,
            "cutoff": sprint.CUTOFF, "updated": "2026-08-02T00:12:00+00:00", **kw}


def test_c15_cocuk_yaziminda_damga_hayatta_kalir(sprint_sandbox):
    """İNVARİANT: çocuk yazımından SONRA da `n_hyp_at_start`/`cfg` okunabilir.

    Düzeltmeden önce ölçüm şuydu: ebeveyn anahtarları [cfg, …, n_hyp_at_start, …] → çocuğun İLK
    `status()` çağrısından sonra damga YOK. Burada aynı sırayı kurup dosyayı okuyoruz."""
    store.write_json(sprint.STATUS_FILE, PARENT_STAMP)
    sprint_run._write_live_status(_child_payload(phase="baseline", progress=0, total=520, n_v1=0))

    st = json.loads((sprint_sandbox / sprint.STATUS_FILE).read_text())
    assert st["phase"] == "baseline", "çocuğun ilerlemesi yazılmalı (koruma yazımı bastırmaz)"
    assert st["n_hyp_at_start"] == 41, "KADANS DAMGASI SİLİNDİ — tetik her gece yanar"
    assert st["cfg"] == {"k_max": 3, "budget": 12}
    # `sprint.status()` okuyucusu da görmeli (should_run oradan okur)
    assert sprint.status()["n_hyp_at_start"] == 41


def test_c15_ard_arda_yazimlar_damgayi_tasimaya_devam_eder(sprint_sandbox):
    """Tek yazım değil, sprint boyunca HER yazım: baseline → search → candidate → done."""
    store.write_json(sprint.STATUS_FILE, PARENT_STAMP)
    for faz in ("baseline", "search", "candidate", "done"):
        sprint_run._write_live_status(_child_payload(phase=faz))
        st = json.loads((sprint_sandbox / sprint.STATUS_FILE).read_text())
        assert st.get("n_hyp_at_start") == 41, f"{faz} yazımında damga düştü"


def test_c15_hata_yolu_da_damgayi_korur(sprint_sandbox):
    """`sprint_run.main()`in istisna yolu sid'siz bir payload yazar. Sprint ÇÖKTÜĞÜNDE kadans
    tabanının da sıfırlanması, çökmeyi "her gece yeniden dene"ye çevirirdi."""
    store.write_json(sprint.STATUS_FILE, PARENT_STAMP)
    sprint_run._write_live_status({"phase": "error", "error": "RuntimeError: x",
                                   "updated": "2026-08-02T00:20:00+00:00"})
    st = json.loads((sprint_sandbox / sprint.STATUS_FILE).read_text())
    assert st["phase"] == "error" and st["n_hyp_at_start"] == 41


def test_c15_baska_sprintin_damgasi_TASINMAZ(sprint_sandbox):
    """Koruma bir UYDURMA KAPISI değildir: dosyadaki kayıt BAŞKA bir sprintinse (sid farklı) o
    sprintin tabanı bu sprintin damgası gibi sunulamaz."""
    store.write_json(sprint.STATUS_FILE, PARENT_STAMP)
    yeni = _child_payload(sid="20260803-235959", phase="baseline")
    sprint_run._write_live_status(yeni)
    st = json.loads((sprint_sandbox / sprint.STATUS_FILE).read_text())
    assert st["sid"] == "20260803-235959"
    assert "n_hyp_at_start" not in st, "başka sprintin tabanı devralındı — ölçülmemiş sayı"


# --------------------------------------------------------------------------------------------
# TAKVİM BOMBASI SÖKÜLDÜ (2026-08-09) — ÖLÇÜLEN KÖK, İKİ KATMANLI
#
# Aşağıdaki kadans testi 2026-08-08'e kadar yeşildi ve 09'da KOD DEĞİŞMEDEN kırmızıya döndü.
# Sebep bir regresyon değil, testin GERÇEK DUVAR SAATİNE bağlı olmasıydı:
#
#   (1) `_child_payload` `started_at`i SABİT bir takvim ânından alıyor ("2026-08-02T00:11:00Z") ve
#       çocuk yazımı ebeveynin `started_at`ini EZİYOR. Testin kendi `simdi = dt.datetime.now(...)`
#       yazımı bu yüzden ÖLÜYDÜ — docstring "sprint BUGÜN koştu (gun=0)" diyordu ama fiilen koşan
#       kurulum hiçbir zaman gun=0 olmadı. İki gerçek bir aradaydı ve kimse ikisini kıyaslamadı.
#   (2) `sprint.should_run` `gun` bacağını ENJEKTE EDİLEN `now`dan DEĞİL, `dt.datetime.now(utc)`
#       ile gerçek saatten hesaplıyor (ÖLÇÜM: sprint.py:400). `now=` parametresi YALNIZ `saat`/
#       `pencere` bacağını taşır (sprint.py:405, 415). Yani testin tarihi çivilediği SANILAN yer
#       tarihi hiç çivilemiyordu.
#
# İkisi birleşince `gun = bugün − 2026-08-02` her gün BİR ARTIYOR: 08-08'de 6 (< 7 → tetik_yok,
# yeşil), 08-09'da 7 (>= SPRINT_STALE_DAYS → `haftalik_taban` MEŞRU yandı, kırmızı). Test bir
# invariant değil, BİR HAFTALIK GERİ SAYIM ölçüyordu.
#
# ÇÖZÜM — MESAFEYİ ÇİVİLE, TAKVİMİ DEĞİL. Üretim kodu bu turda dokunulmaz, ve `now=` bacağı (2)
# yüzünden `gun`ü zaten taşıyamıyor. Küresel bir saat şimi (`dt.datetime` yamalamak) tek seçenek
# DEĞİL ve daha pahalı olurdu: stdlib'i test süresince mutasyona uğratır, `should_run`un çağırdığı
# her şey (auto_config, status) o sahte saati görürdü. Onun yerine fikstür `started_at`i GERÇEK
# ŞİMDİYE GÖRE geriye alır. Kadansın eşiği (`SPRINT_STALE_DAYS`) zaten bir TAKVİM TARİHİ değil bir
# MESAFEDİR; sınanan şeyi doğrudan çivilemek, etrafındaki saati taklit etmekten dürüsttür.
# --------------------------------------------------------------------------------------------
def _taban(gecen_gun: int) -> str:
    """`started_at` damgası: ŞİMDİDEN tam `gecen_gun` gün geride.

    YARIM GÜN YASTIK BİLEREK: `should_run` farkı `.days` ile TABANA YUVARLAR, yani `gecen_gun`
    günlük düz bir fark testin kendi koşum süresi kadar (ε) fazla olur ve `.days` yine `gecen_gun`
    verir — ama yastıksız bir kurulum, "ε neden sorun değil" sorusunu her okuyucuya yeniden
    sordurur. 12 saatlik yastıkla hüküm ε'a hiç bağlı olmaz: 6g12s → `.days == 6`, 7g12s → 7."""
    an = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=gecen_gun, hours=12)
    return an.isoformat(timespec="seconds")


def _c15_kadans_karari(sprint_sandbox, monkeypatch, gecen_gun: int) -> dict:
    """Canlı ölçümün birebir kopyası, TEK değişkeni son sprintin üstünden geçen gün sayısı:
    41 hipotez, damga 41, saat gece penceresinde, çocuk yazımı yapılmış.

    `started_at` İKİ KEZ yazılır ve ikisi de gerekli: ebeveyn kaydına (should_run'ın okuduğu yer)
    ve çocuk payload'ına (yazım ebeveyninkini ezer — kusurun ta kendisi). Yalnız birini vermek,
    sökülen bombanın diğer yarısını yerinde bırakırdı."""
    from meridian import hermes
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)
    (sprint_sandbox / "hypotheses.jsonl").write_text(
        "".join(json.dumps({"id": f"H{i:05d}"}) + "\n" for i in range(41)))
    taban = _taban(gecen_gun)
    store.write_json(sprint.STATUS_FILE, {**PARENT_STAMP, "started_at": taban})

    # ÇOCUK YAZIMI — kusurun tetiklendiği an. FAZ 'done' (v235 uyarlaması, 2026-08-12): bu iki
    # kadans testi DAMGA disiplinini (taze=0, haftalık eşik) ölçer ve karar hâli "son sprint BİTTİ,
    # kadans yeni tur düşünüyor"dur. Eski fikstür 'baseline' + ölü pid (999999) taşıyordu — v235
    # yetim yasasından beri o hâl YARIDA KALMIŞ sprint demektir ve kadans onu MEŞRU olarak
    # `yetim_sprint_yeniden` ile yeniden başlatır (canlı vakanın ta kendisi; kapsamı
    # test_ogrenme_katmani_durmasi_v235). Damga-koruma mekaniği fazdan bağımsızdır — buradaki
    # iddiaların hiçbiri değişmez.
    sprint_run._write_live_status(_child_payload(phase="done", progress=8, total=520,
                                                 n_v1=0, started_at=taban))

    # `now` YALNIZ SAATİ taşır (sprint.py:405/415) — 23:00 pencere İÇİNDE (22→06). Gün bacağını
    # taşımadığı ölçüldü; tarih burada bir çivi DEĞİLDİR ve öyleymiş gibi okunmamalı.
    return sprint.should_run(now=dt.datetime(2026, 8, 2, 23, 30))


def test_c15_maybe_start_tabani_sifirlanmaz_tetik_her_gece_yanmaz(sprint_sandbox, monkeypatch):
    """ASIL SONUÇ: çocuk yazımından sonra `should_run` HAFTALIK DİSİPLİNİ korumalı.

    Kusurlu kodda `taze = 41 − 0 = 41 ≥ 5` → haftalık taban dolmadan "taze_aday_birikimi" ile
    tetik yanardı. Taban 6 GÜN: eşiğin (7) hemen ALTINDA, yani tetiği tutan tek şey damganın
    hayatta kalması."""
    karar = _c15_kadans_karari(sprint_sandbox, monkeypatch, gecen_gun=6)
    assert karar["gecen_gun"] == 6, f"taban kaymış — takvim bağımlılığı geri gelmiş olabilir: {karar}"
    assert karar["taze_hipotez"] == 0, f"taban sıfırlandı: {karar}"
    assert karar["kos"] is False, f"tetik yandı: {karar}"
    assert karar["sebep"].startswith("tetik_yok"), karar["sebep"]


def test_c15_haftalik_taban_7_GUNDE_yanar_ama_sebebi_TAZE_BIRIKIM_DEGIL(sprint_sandbox, monkeypatch):
    """ÇİVİNİN İKİNCİ YÖNÜ — bomba sınıfı bir daha kurulmasın diye.

    Tek yönlü bir çivi ("kos False olsun") kadansı BÜSBÜTÜN ölü bir hâle karşı kör kalırdı: damga
    korumasının haftalık tetiği de susturması aynı testi yeşil bırakırdı. Burası tetiğin GERÇEKTEN
    yandığını ölçer ve asıl ayrımı yapar: 7. günde `kos` True olmalı ama sebebi `haftalik_taban`
    OLMALI, `taze_aday_birikimi` OLMAMALI — C15 kusuru tam olarak ikincisini üretiyordu.

    `taze_hipotez == 0` burada da çivilidir ve asıl kanıt odur: tetik yandığı hâlde taban HÂLÂ 41
    okunuyor, yani sprint meşru bir haftalık kadansla başlıyor, sıfırlanmış bir sayaçla değil."""
    karar = _c15_kadans_karari(sprint_sandbox, monkeypatch, gecen_gun=7)
    assert karar["gecen_gun"] == 7, f"taban kaymış: {karar}"
    assert karar["taze_hipotez"] == 0, f"damga düştü — tetik doğru sebeple yanmıyor: {karar}"
    assert karar["kos"] is True, f"haftalık taban dolmuşken kadans susuyor: {karar}"
    assert karar["sebep"] == "haftalik_taban", \
        f"tetik yandı ama YANLIŞ sebeple — C15 kusurunun imzası budur: {karar['sebep']}"


# ==================================================================================================
# C4 — BAŞARISIZ MİGRASYON GERİDE AKTİF-BOŞ DB BIRAKMAZ
# ==================================================================================================
TRADE_A = {"id": "T00001", "ticker": "AAPL", "side": "long", "entry": 100.5, "qty": 10,
           "strategy_version": 4, "regime": "trend_up", "score": 72}
TRADE_B = {"id": "T00002", "ticker": "MSFT", "side": "long", "entry": 310.0, "qty": 3,
           "strategy_version": 4, "regime": "trend_up", "score": 65}
BOOK = {"cash": 91234.5, "realized_pnl": -8765.5, "last_id": 42,
        "positions": {"AAPL": {"qty": 10}}, "armed": [], "pending_exits": {},
        "last_date": "2026-08-01", "day_start_equity": 91234.5}
SB = {"current_version": 3, "versions": {"3": {"live_score": -0.0089, "n_trades": 2}}}


@pytest.fixture
def db_sandbox(sandbox_state):
    yield sandbox_state
    storage.close_connections()


def _seed(state) -> None:
    (state / "trades.jsonl").write_text(json.dumps(TRADE_A) + "\n" + json.dumps(TRADE_B) + "\n")
    (state / "trade_plans.jsonl").write_text("")
    (state / "portfolio.json").write_text(json.dumps(BOOK))
    (state / "scoreboard.json").write_text(json.dumps(SB))


def _failed_dbler(state) -> list:
    return sorted(p.name for p in state.iterdir()
                  if p.name.startswith(storage.DB_NAME + dbmigrate.FAILED_SUFFIX))


def test_c4_kaynak_bozuk_yolunda_db_kenara_alinir(db_sandbox):
    """KAYNAK_BOZUK: rapor "hiçbir varlık taşınmadı" derken arka uç DEĞİŞMİŞ OLAMAZ."""
    _seed(db_sandbox)
    (db_sandbox / "portfolio.json").write_text("{ bozuk json")

    rapor = dbmigrate.apply()

    assert rapor["ok"] is False and "portfolio.json" in rapor["hata"]
    # 1) DB DEVREDE DEĞİL — kusurun kalbi buydu (eskiden True dönüyordu)
    assert storage.active(storage.TRADES) is False
    assert store.db_backed("trades.jsonl") is False
    # 2) Dosya kenara alındı; kanonik yolda DB YOK
    assert not storage.db_path().exists()
    assert rapor["karantina"]["yapildi"] is True and rapor["karantina"]["db_yeni"] is True
    assert rapor["karantina"]["aktif"] is False
    assert len(_failed_dbler(db_sandbox)) >= 1, "kenara alınan DB dosyası yok"
    # 3) ALTI DEFTER SESSİZCE BOŞ OKUNMUYOR — dosya arka ucundan GERÇEK satırlar gelir
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]
    assert store.read_json("portfolio.json", None) is None    # bozuk kaynak DÜRÜSTÇE okunamaz
    assert store.read_json("scoreboard.json", {}) == SB
    # 4) Kaynak dosyalar DOKUNULMAMIŞ (ne silinmiş ne .migrated olmuş)
    for ad in ("trades.jsonl", "trade_plans.jsonl", "portfolio.json", "scoreboard.json"):
        assert (db_sandbox / ad).exists(), ad
        assert not (db_sandbox / (ad + dbmigrate.MIGRATED_SUFFIX)).exists(), ad


def test_c4_parite_tutmadi_yolunda_db_kenara_alinir(db_sandbox):
    """PARİTE_TUTMADI dalı KAYNAK_BOZUK ile aynı hükmü almalı — iki dal, tek yasa.

    YAMA `monkeypatch` FİKSTÜRÜNE BAĞLANMAZ (bu depoda belgeli ders): `monkeypatch.undo()`
    `sandbox_state`in `config.STATE` yamasını da sökerdi ve test canlı `state/`e bakmaya başlardı.
    Kendi yamasını kendi kurar, `try/finally` ile kendi söker."""
    _seed(db_sandbox)
    gercek = storage.read_entity

    def _bozuk(name):
        out = gercek(name)
        return out[:-1] if name == "trades.jsonl" and isinstance(out, list) else out

    storage.read_entity = _bozuk
    try:
        rapor = dbmigrate.apply()
    finally:
        storage.read_entity = gercek

    assert rapor["ok"] is False and "PARİTE TUTMADI" in rapor["hata"]
    assert rapor["karantina"]["yapildi"] is True
    assert storage.active(storage.TRADES) is False and not storage.db_path().exists()
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]
    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]
    assert not (db_sandbox / ("trades.jsonl" + dbmigrate.MIGRATED_SUFFIX)).exists()


def test_c4_sema_migrasyon_transaction_ININ_ICINDE_kurulur(db_sandbox):
    """Kusurun MEKANİZMASI: şema hata dalından ÖNCE COMMIT ediliyordu. Başarısız bir koşudan sonra
    kanonik yolda ne şema ne dosya kalmalı; kenara alınan kopyada da şema OLMAMALI (geri alındı)."""
    _seed(db_sandbox)
    (db_sandbox / "portfolio.json").write_text("{ bozuk json")
    dbmigrate.apply()

    assert not storage.db_path().exists()
    kenar = db_sandbox / _failed_dbler(db_sandbox)[0]
    import sqlite3
    c = sqlite3.connect(str(kenar))
    try:
        tablolar = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    finally:
        c.close()
    assert "trades" not in tablolar and "schema_version" not in tablolar, \
        f"şema transaction DIŞINDA COMMIT edilmiş: {tablolar}"


def test_c4_kuru_kosu_db_yaratmaz(db_sandbox):
    """`plan()` beyanı: "Hiçbir bayt yazılmaz, DB açılmaz (yoksa yaratılmaz)". `db_state()` eskiden
    bu yolda `ensure_schema` çağırıyordu; beyan ancak şimdi doğru."""
    _seed(db_sandbox)
    rapor = dbmigrate.plan()
    assert rapor["db_var"] is False and not storage.db_path().exists()
    assert storage.active(storage.TRADES) is False


def test_c4_onceden_VAR_OLAN_db_kenara_ALINMAZ(db_sandbox):
    """KARANTİNANIN SINIRI. Dosya bu koşudan önce de varsa TAŞINMIŞ defterler içerebilir; onu
    kenara almak hata yolunu veri kaybına çevirirdi. Kurulum: başarılı migrasyon → sonra HENÜZ
    taşınmamış bir varlık (shadow_books.json) BOZUK yazılır → ikinci koşu KAYNAK_BOZUK ile düşer."""
    _seed(db_sandbox)
    assert dbmigrate.apply()["ok"] is True
    assert store.db_backed("trades.jsonl") is True

    (db_sandbox / "shadow_books.json").write_text("{ bozuk json")
    rapor = dbmigrate.apply()

    assert rapor["ok"] is False and rapor["db_yeni"] is False
    assert rapor["karantina"]["yapildi"] is False and rapor["karantina"]["not"]
    # DB YERİNDE ve taşınmış defter OKUNUYOR — hata yolu veri kaybettirmedi
    assert storage.db_path().exists() and storage.active(storage.TRADES) is True
    assert [t["id"] for t in store.read_jsonl("trades.jsonl")] == ["T00001", "T00002"]
    assert store.read_json("portfolio.json", {})["cash"] == BOOK["cash"]
    assert _failed_dbler(db_sandbox) == []


def test_c4_basarili_yol_REGRESYONSUZ(db_sandbox):
    """Parite-digest yolu aynen çalışmalı: taşınır, digestler eşleşir, kaynaklar `.migrated` olur,
    ikinci koşu `zaten_tasindi` der ve karantina HİÇ devreye girmez."""
    _seed(db_sandbox)
    once = {"trades": store.read_jsonl("trades.jsonl"),
            "pf": store.read_json("portfolio.json", {}),
            "sb": store.read_json("scoreboard.json", {})}

    r1 = dbmigrate.apply()
    assert r1["ok"] is True and r1["yazildi"] is True and "karantina" not in r1
    esles = {p["varlik"]: p for p in r1["parite"]}
    for ad in ("trades.jsonl", "portfolio.json", "scoreboard.json"):
        assert esles[ad]["durum"] == "tasindi", esles[ad]
        assert esles[ad]["kaynak_digest"] == esles[ad]["db_digest"], ad
    assert store.db_backed("trades.jsonl") is True and storage.schema_version() == 1
    sonra = {"trades": store.read_jsonl("trades.jsonl"),
             "pf": store.read_json("portfolio.json", {}),
             "sb": store.read_json("scoreboard.json", {})}
    for k in once:
        assert dbmigrate.digest(once[k]) == dbmigrate.digest(sonra[k]), k
    for ad in ("trades.jsonl", "portfolio.json", "scoreboard.json"):
        assert (db_sandbox / (ad + dbmigrate.MIGRATED_SUFFIX)).exists(), ad
    # `--durum` kanıtı: migrasyonun parmak izi DB'de duruyor
    durum = {r["varlik"]: r for r in dbmigrate.db_state()}
    assert durum["trades.jsonl"]["migrated_at"] and durum["trades.jsonl"]["kaynak_digest"]

    r2 = dbmigrate.apply()
    assert r2["ok"] is True and r2["yazildi"] is False and "karantina" not in r2
    assert all(p["durum"] in ("zaten_tasindi", "kaynak_yok") for p in r2["parite"])
    assert len(store.read_jsonl("trades.jsonl")) == 2, "satır İKİYE katlandı"


def test_c4_karantina_wal_ve_shm_dosyalarini_da_tasir(db_sandbox):
    """Ana dosya yeniden adlandırılıp `meridian.db-wal` yerinde kalsaydı, İLERİDE doğacak taze bir
    `meridian.db` bayat bir WAL'la eşleşirdi."""
    _seed(db_sandbox)
    (db_sandbox / "portfolio.json").write_text("{ bozuk json")
    dbmigrate.apply()
    kalanlar = [p.name for p in db_sandbox.iterdir()
                if p.name.startswith(storage.DB_NAME) and dbmigrate.FAILED_SUFFIX not in p.name]
    assert kalanlar == [], f"kanonik DB adıyla dosya kaldı: {kalanlar}"


def test_c4_canli_state_dokunulmadi():
    """DÜRÜSTLÜK KAPISI: bu dosyanın hiçbir testi canlı `state/meridian.db`ye dokunmaz. `config.STATE`
    sandbox'a yamalıyken `db_path()` her çağrıda oradan türer — bu testte yama YOKTUR, yani okunan
    yol CANLI yoldur ve yalnız VARLIĞI sorulur (açılmaz, yaratılmaz)."""
    assert storage.db_path() == config.STATE / storage.DB_NAME
    assert not any(p.name.startswith(storage.DB_NAME + dbmigrate.FAILED_SUFFIX)
                   for p in config.STATE.iterdir() if p.is_file()), \
        "canlı state'te karantina dosyası var — bir test sandbox dışına yazmış"

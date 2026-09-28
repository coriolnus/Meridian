"""v582 — TSK-020 Kademe C düzeltme turu 2: KAPSAMLI geri alma (F1) + öğrenme süreci kapısı (F2).

BRIEF: scratchpad `tsk020c-tur2-brief.md` (Rol-1, 2026-09-28). Tur 1 bulgusu (rapor §8.4): `dbmigrate --geri-al` HEPSİ-YA-HİÇ'tir —
DB'nin tamamını kenara alır, Kademe A+B'nin altı defterini de dosyaya döndürür; onların 2026-07-31'den beri DB'ye yazılmış
satırları arşivde YOKTUR. Kademe C'nin canlı göçünden önce şarttır:

F1 — `--geri-al --varlik a,b`: YALNIZ listelenen (damga kapılı) varlıkların `migrated_at`/`source_digest` damgası temizlenir
     (okuma kapısı onları dosyaya döndürür), `.migrated` arşivleri kanonik ada döner, tablo satırları SİLİNMEZ (kanıt), DB
     dosyası TAŞINMAZ; rapor varlık başına DB↔arşiv satır + digest farkını basar. Eski altı / bilinmeyen ad → RET.
     Varsayılan (`--varlik`siz) davranış aynı, ama çıktı "Kademe A+B'yi de geri alır" uyarısını taşır.
F2 — canlı-süreç kapısı öğrenme sürecini (`meridian-learn`: `python -m meridian.learn_run`) de görür; `--zorla` ezer;
     `barrepair._worker_running` (paylaşılan yardımcı) DEĞİŞMEZ.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import re
import subprocess

import pytest

from meridian import barrepair, dbmigrate, storage, store

YENI = ("hypotheses.jsonl", "validation_ledger.jsonl")
ESKI = ("trades.jsonl", "trade_plans.jsonl", "scoreboard.json", "portfolio.json",
        "equity_curve.json", "shadow_books.json")
HYP, VAL = YENI
KOK = pathlib.Path(__file__).resolve().parent.parent

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
    for i in range(1, 3)
]
GOC_SONRASI = dict(VAL_SATIRLAR[0], etiket="goc-sonrasi", ts="2026-09-29T10:00:00+00:00")
TRADE = {"id": "T00001", "ts_open": "2026-01-02", "ts_close": "2026-01-09", "ticker": "AAPL",
         "side": "long", "r_multiple": 1.5, "strategy_version": 4}
PLAN = {"id": "P-2026-01-02-AAPL", "date": "2026-01-02", "ticker": "AAPL", "side": "long"}


@pytest.fixture
def db_sandbox(sandbox_state, monkeypatch):
    monkeypatch.delenv("MERIDIAN_DB", raising=False)
    store._BAYAT_SUPURULDU.clear()
    yield sandbox_state
    storage.close_connections()
    store._BAYAT_SUPURULDU.clear()


def _yaz(state, ad, satirlar):
    (state / ad).write_text("".join(json.dumps(r) + "\n" for r in satirlar))


def _goc(state):
    """Canlının D6-2 SONRASI hâli: sekiz varlık DB'de ve damgalı, kaynaklar `.migrated`."""
    _yaz(state, "trades.jsonl", [TRADE])
    _yaz(state, "trade_plans.jsonl", [PLAN])
    for ad, doc in (("portfolio.json", {"cash": 1.0}), ("scoreboard.json", {"versions": {}}),
                    ("equity_curve.json", {"version": 1, "points": [["2026-01-02", 100.0]]}),
                    ("shadow_books.json", {"v": 1})):
        (state / ad).write_text(json.dumps(doc))
    _yaz(state, HYP, HYP_SATIRLAR)
    _yaz(state, VAL, VAL_SATIRLAR)
    r = dbmigrate.apply()
    assert r["ok"] is True and sorted(r["tasinan"]) == sorted(ESKI + YENI), r.get("hata")
    for ad in ESKI + YENI:
        assert store.db_backed(ad) is True, ad


def _eski_fotograf(state):
    """Eski altının tam izi: damga (migrated_at, source_digest, rev, n), tablo içeriği (digest), dosya adları."""
    out = {}
    for ad in ESKI:
        m = storage.meta(ad)
        out[ad] = {"migrated_at": m["migrated_at"], "source_digest": m["source_digest"],
                   "rev": m["rev"], "n": m["n"],
                   "tablo": dbmigrate.digest(storage.read_entity(ad)),
                   "arsiv": (state / (ad + storage.MIGRATED_SUFFIX)).exists(),
                   "kanonik": (state / ad).exists()}
    return out


def _olaylar(state, event):
    p = state / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines()
            if x.strip() and json.loads(x).get("event") == event]


# ---- F1: KISITLI GERİ ALMA ----------------------------------------------------------------------
def test_kisitli_geri_al_yalniz_listelenenlere_dokunur(db_sandbox):
    _goc(db_sandbox)
    store.append_jsonl(VAL, GOC_SONRASI)            # göç SONRASI DB'ye yazılmış satır (arşivde YOK)
    once = _eski_fotograf(db_sandbox)

    rapor = dbmigrate.rollback_kisitli([HYP, VAL])

    assert rapor["ok"] is True and rapor["kip"] == "kisitli"
    # DB dosyası YERİNDE, kenara alınmadı
    assert storage.db_path().exists() and rapor["db_kenara"]["yapildi"] is False
    assert not [p for p in db_sandbox.iterdir() if dbmigrate.ROLLEDBACK_SUFFIX in p.name]
    # eski altı BİT-BİT aynı: damga, tablo, dosyalar
    assert _eski_fotograf(db_sandbox) == once
    for ad in ESKI:
        assert store.db_backed(ad) is True, ad
    # iki defter: damga temiz, arşiv kanonik adda, tablo satırları SİLİNMEDİ (kanıt)
    for ad in YENI:
        m = storage.meta(ad)
        assert m["migrated_at"] is None and m["source_digest"] is None, ad
        assert (db_sandbox / ad).exists() and not (db_sandbox / (ad + storage.MIGRATED_SUFFIX)).exists()
    assert len(storage.read_rows(HYP)) == len(HYP_SATIRLAR)
    assert [r["etiket"] for r in storage.read_rows(VAL)] == ["k=1", "k=2", "goc-sonrasi"]
    assert sorted(rapor["damgasi_kaldirilan"]) == sorted(YENI)
    assert sorted(rapor["geri_donen"]) == sorted(YENI)


def test_geri_al_sonrasi_store_iki_defteri_dosyadan_okur(db_sandbox):
    _goc(db_sandbox)
    store.append_jsonl(VAL, GOC_SONRASI)
    dbmigrate.rollback_kisitli([HYP, VAL])
    for ad in YENI:
        assert store.db_backed(ad) is False, ad
    assert dbmigrate.digest(store.read_jsonl(HYP)) == dbmigrate.digest(HYP_SATIRLAR)
    assert [r["etiket"] for r in store.read_jsonl(VAL)] == ["k=1", "k=2"]
    # YENİ SÜREÇ gözü (önbelleksiz): yine dosyadan; süzgeç iki kanonik dosyaya DOKUNMAZ
    storage.close_connections()
    store._BAYAT_SUPURULDU.clear()
    assert store.db_backed("trades.jsonl") is True       # süzgeç tetiği
    for ad in YENI:
        assert store.db_backed(ad) is False and (db_sandbox / ad).exists(), ad
    assert [r["etiket"] for r in store.read_jsonl(VAL)] == ["k=1", "k=2"]
    assert _olaylar(db_sandbox, "db_aktif_kanonik_dosya_gocsuz") == []
    assert _olaylar(db_sandbox, "bayat_defter_arsivlendi") == []


def test_goc_sonrasi_eklenen_satir_raporda_kayip_degil_dbde_duruyor(db_sandbox):
    _goc(db_sandbox)
    store.append_jsonl(VAL, GOC_SONRASI)
    rapor = dbmigrate.rollback_kisitli([HYP, VAL])
    v = {r["varlik"]: r for r in rapor["varliklar"]}
    assert v[VAL]["db_n"] == 3 and v[VAL]["dosya_n"] == 2 and v[VAL]["fark"] == 1
    assert v[VAL]["digest_esit"] is False
    assert v[HYP]["fark"] == 0 and v[HYP]["digest_esit"] is True
    assert [f["varlik"] for f in rapor["fark_var"]] == [VAL]
    assert "DB'de duruyor" in rapor["beyan"] and "validation_ledger" in rapor["beyan"]
    olay = _olaylar(db_sandbox, "sqlite_ledger_rolled_back_kisitli")
    assert len(olay) == 1 and sorted(olay[0]["damgasi_kaldirilan"]) == sorted(YENI)


def test_kisitli_geri_al_bir_defterle_digerine_dokunmaz(db_sandbox):
    _goc(db_sandbox)
    dbmigrate.rollback_kisitli([VAL])
    assert store.db_backed(VAL) is False and store.db_backed(HYP) is True
    assert storage.meta(HYP)["migrated_at"] is not None
    assert (db_sandbox / (HYP + storage.MIGRATED_SUFFIX)).exists() and not (db_sandbox / HYP).exists()


def test_eski_alti_ya_da_bilinmeyen_ad_reddedilir_ve_hicbir_sey_degismez(db_sandbox, monkeypatch, capsys):
    _goc(db_sandbox)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: False)
    once = _eski_fotograf(db_sandbox)
    damga = {ad: storage.meta(ad)["migrated_at"] for ad in YENI}
    for arg in ("trades.jsonl", "yok.jsonl", f"{HYP},trades.jsonl", ""):
        assert dbmigrate.main(["--geri-al", "--varlik", arg]) == 2, arg
        assert "REDDEDİLDİ" in capsys.readouterr().err, arg
    assert _eski_fotograf(db_sandbox) == once
    assert {ad: storage.meta(ad)["migrated_at"] for ad in YENI} == damga
    assert not (db_sandbox / HYP).exists()
    with pytest.raises(ValueError):
        dbmigrate.rollback_kisitli(["trades.jsonl"])
    with pytest.raises(ValueError):
        dbmigrate.rollback_kisitli([])
    # mekanizma da kendini korur: eski varlığın damgası sökülemez (sonraki --uygula tablosunu EZERDİ)
    with pytest.raises(ValueError):
        storage.unmark_migrated("trades.jsonl")
    assert storage.meta("trades.jsonl")["migrated_at"] == once["trades.jsonl"]["migrated_at"]


def test_varlik_bayragi_geri_al_olmadan_reddedilir(db_sandbox, monkeypatch, capsys):
    _goc(db_sandbox)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: False)
    assert dbmigrate.main(["--uygula", "--varlik", HYP]) == 2
    assert dbmigrate.main(["--varlik", HYP]) == 2
    assert "REDDEDİLDİ" in capsys.readouterr().err
    assert storage.meta(HYP)["migrated_at"] is not None


def test_cli_kisitli_geri_al_ve_tekrar_goc_parite_ile_gecer(db_sandbox, monkeypatch, capsys):
    """Operatör biçimi: `--geri-al --varlik a,b` → rapor DB↔arşiv farkını basar → yeniden `--uygula` parite ile geçer
    ve tabloda DAHA ÖNCE satır olduğunu (ezilen kanıt) raporlar."""
    _goc(db_sandbox)
    store.append_jsonl(VAL, GOC_SONRASI)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: False)
    capsys.readouterr()

    assert dbmigrate.main(["--geri-al", "--varlik", f"{HYP}, {VAL}"]) == 0
    out = capsys.readouterr().out
    with capsys.disabled():
        print("\n" + out)
    assert "KISITLI" in out and "Kademe A+B" not in out
    assert any(s.split()[:1] == [VAL] and " 3 " in f" {s} " and " 2 " in f" {s} " for s in out.splitlines())
    assert "DB'de duruyor" in out

    r = dbmigrate.apply()
    assert r["ok"] is True, r.get("hata")
    p = {x["varlik"]: x for x in r["parite"]}
    for ad in YENI:
        assert p[ad]["durum"] == "tasindi" and p[ad]["kaynak_digest"] == p[ad]["db_digest"], p[ad]
    for ad in ESKI:
        assert p[ad]["durum"] == "zaten_tasindi", ad
    assert {e["varlik"]: e["onceki_db_n"] for e in r["ezilen"]} == {HYP: 2, VAL: 3}
    assert store.db_backed(VAL) is True
    assert [x["etiket"] for x in store.read_jsonl(VAL)] == ["k=1", "k=2"]


def test_tam_geri_al_davranisi_ayni_ama_kademe_ab_uyarisi_tasir(db_sandbox, monkeypatch, capsys):
    _goc(db_sandbox)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: False)
    capsys.readouterr()
    assert dbmigrate.main(["--geri-al"]) == 0
    out = capsys.readouterr().out
    assert "Kademe A+B" in out
    assert not storage.db_path().exists()                  # hepsi-ya-hiç: DB kenarda (davranış aynı)
    for ad in ESKI + YENI:
        assert (db_sandbox / ad).exists(), ad


def test_tam_geri_al_raporu_uyariyi_alan_olarak_da_tasir(db_sandbox):
    _goc(db_sandbox)
    rapor = dbmigrate.rollback()
    assert set(rapor["kapsam_uyarisi"]["eski_varliklar"]) == set(ESKI)
    assert "Kademe A+B" in rapor["kapsam_uyarisi"]["metin"]


def test_kisitli_geri_al_idempotent(db_sandbox):
    _goc(db_sandbox)
    dbmigrate.rollback_kisitli([HYP, VAL])
    ikinci = dbmigrate.rollback_kisitli([HYP, VAL])
    assert ikinci["ok"] is True and ikinci["geri_donen"] == [] and ikinci["damgasi_kaldirilan"] == []
    assert "GERİ ALINACAK BİR ŞEY YOK" in ikinci["beyan"]
    assert store.db_backed(HYP) is False and (db_sandbox / HYP).exists()


def test_arsivi_kayip_damgali_varligin_damgasi_kaldirilmaz(db_sandbox):
    """Kanonik dosyası OLMAYAN varlığı dosyaya çevirmek BOŞ okumadır (R1'in kendisi) — damga kalır, rapor düşer."""
    _goc(db_sandbox)
    (db_sandbox / (HYP + storage.MIGRATED_SUFFIX)).rename(db_sandbox / "baska_yere.jsonl")
    rapor = dbmigrate.rollback_kisitli([HYP, VAL])
    assert rapor["ok"] is False
    assert storage.meta(HYP)["migrated_at"] is not None and store.db_backed(HYP) is True
    assert store.db_backed(VAL) is False                    # diğeri yine geri alındı
    assert HYP not in rapor["damgasi_kaldirilan"]


def test_kanonik_adi_isgal_eden_ayrisik_dosya_kenara_alinir(db_sandbox):
    _goc(db_sandbox)
    _yaz(db_sandbox, VAL, [dict(VAL_SATIRLAR[0], etiket="ayrisik")])
    rapor = dbmigrate.rollback_kisitli([VAL])
    rec = {r["varlik"]: r for r in rapor["varliklar"]}[VAL]
    assert rec["ayrisik_kenara"] and (db_sandbox / rec["ayrisik_kenara"]).exists()
    assert [r["etiket"] for r in store.read_jsonl(VAL)] == ["k=1", "k=2"]


def test_kisitli_geri_al_canli_surec_kapisindan_gecer(db_sandbox, monkeypatch):
    _goc(db_sandbox)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: False)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: True)
    assert dbmigrate.main(["--geri-al", "--varlik", HYP]) == 2
    assert storage.meta(HYP)["migrated_at"] is not None
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: True)
    assert dbmigrate.main(["--geri-al", "--varlik", HYP]) == 2
    assert storage.meta(HYP)["migrated_at"] is not None
    assert dbmigrate.main(["--geri-al", "--varlik", HYP, "--zorla"]) == 0
    assert storage.meta(HYP)["migrated_at"] is None


# ---- F2: ÖĞRENME SÜRECİ KAPISI ------------------------------------------------------------------
def test_uygula_ogrenme_sureci_kosarken_reddedilir_zorla_gecer(db_sandbox, monkeypatch, capsys):
    _yaz(db_sandbox, HYP, HYP_SATIRLAR)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: True)
    assert dbmigrate.main(["--uygula"]) == 2
    err = capsys.readouterr().err
    assert "REDDEDİLDİ" in err and "meridian-learn" in err
    assert not storage.db_path().exists(), "reddedilen koşu DB'yi yarattı"
    assert (db_sandbox / HYP).exists()
    assert dbmigrate.main(["--uygula", "--zorla"]) == 0
    assert store.db_backed(HYP) is True


def test_tam_geri_al_ogrenme_sureci_kosarken_reddedilir(db_sandbox, monkeypatch):
    _goc(db_sandbox)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: False)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: True)
    assert dbmigrate.main(["--geri-al"]) == 2
    assert storage.db_path().exists()


def test_kuru_kosu_ve_durum_kapidan_etkilenmez(db_sandbox, monkeypatch):
    """Kapı YALNIZ yazan kiplerde: kuru koşu ve `--durum` öğrenme koşarken de okunabilmeli (triyaj)."""
    _yaz(db_sandbox, HYP, HYP_SATIRLAR)
    monkeypatch.setattr(dbmigrate, "_worker_running", lambda: True)
    monkeypatch.setattr(dbmigrate, "_ogrenme_sureci_kosuyor", lambda: True)
    assert dbmigrate.main([]) == 0
    assert dbmigrate.main(["--durum"]) == 0


def test_ogrenme_yoklamasi_pgrep_ile_olcer_ve_olculemezse_kosuyor_sayar(monkeypatch):
    cagri = {}

    class _R:
        def __init__(self, out):
            self.stdout = out

    def _run(argv, **kw):
        cagri["argv"] = argv
        return _R(cagri.get("cikti", ""))

    monkeypatch.setattr(dbmigrate.subprocess, "run", _run)
    cagri["cikti"] = "4242\n"
    assert dbmigrate._ogrenme_sureci_kosuyor() is True
    assert cagri["argv"][:2] == ["pgrep", "-f"] and cagri["argv"][2] == dbmigrate.OGRENME_SURECI_DESENI
    cagri["cikti"] = ""
    assert dbmigrate._ogrenme_sureci_kosuyor() is False

    def _patla(argv, **kw):
        raise OSError("pgrep yok")

    monkeypatch.setattr(dbmigrate.subprocess, "run", _patla)
    assert dbmigrate._ogrenme_sureci_kosuyor() is True, "ölçülemeyen yoklama 'koşmuyor' sayıldı"
    monkeypatch.setattr(dbmigrate.subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("pgrep", 5)))
    assert dbmigrate._ogrenme_sureci_kosuyor() is True


def _execstart(birim: str) -> str:
    satirlar = [s for s in (KOK / "deploy/oracle-a1" / birim).read_text().splitlines()
                if s.startswith("ExecStart=")]
    assert len(satirlar) == 1, (birim, satirlar)
    return satirlar[0].split("=", 1)[1]


def test_ogrenme_deseni_birimin_execstartindan_turer():
    """Ayrışma çivisi (tek-kaynak yasası): desen UYDURULMADI — `meridian-learn.service` ExecStart'ını eşler; ana birimi
    (`meridian.service`, uvicorn) EŞLEMEZ, `barrepair`in deseni de öğrenme birimini eşlemez (iki kapı ayrık)."""
    ogrenme = _execstart("meridian-learn.service")
    ana = _execstart("meridian.service")
    assert re.search(dbmigrate.OGRENME_SURECI_DESENI, ogrenme), ogrenme
    assert not re.search(dbmigrate.OGRENME_SURECI_DESENI, ana), ana
    assert re.search("uvicorn meridian.api", ana) and not re.search("uvicorn meridian.api", ogrenme)
    # desen dosya YOLUNU (meridian/learn_run.py — editörde açık dosya, grep) eşlemez: nokta LİTERAL
    assert not re.search(dbmigrate.OGRENME_SURECI_DESENI, "vim meridian/learn_run.py")


def test_barrepair_worker_running_anlami_degismedi():
    """Paylaşılan yardımcı (barrepair/ledgerstamp/sermaye tüketir) DOKUNULMADI: yalnız uvicorn arar."""
    src = inspect.getsource(barrepair._worker_running)
    assert '"uvicorn meridian.api"' in src and "learn" not in src

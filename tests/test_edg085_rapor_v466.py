"""test_edg085_rapor_v466.py — EDG-2026-085 Senaryo-A ÇEVRİMDIŞI RAPOR ARACI çivileri.

Araç: research/olcumler/edg085_icra_ani_quote/rapor.py (KOMUT SATIRI sözleşmesi: gövde `kos(argv)`).
Kart: research/cards/EDG-2026-085-icra-ani-quote-kaydi-senaryo-a.yaml (eşikler burada DEĞİŞTİRİLMEZ,
araçtan OKUNUR — kopya iki yerde sessizce ayrışır).

ÖLÇÜM NOTLARI (plan yer tutucuları düzeltildi, 2026-09-13):
  * `state/intraday_bars/<gün>.jsonl` satırı `{"ts": ..., "bars": {SEMBOL: {o,h,l,c,v,vw,n,t}}}`
    biçimindedir (bararchive'in `archive_frame` gövdesinden ölçüldü) — plan taslağındaki
    "ticker, t, o, h, l, c" düz satırı DEĞİL.
  * `taban.jsonl` satırında `healthz_p95_ms` alanı YOKTUR (örnekleyici 5 istekten p50 ve maks
    yazar); p95 örnekler ARASINDA, `healthz_p50_ms` dağılımından türetilir — kartın ADIM-0 (3)
    kaydının yaptığı hesabın aynısı.
  * `trades` tablosunun kolonları `storage._COLS` kaydından ölçüldü; bu dosya yalnız gereken üçünü
    (plan_id, entry, extra_json) taşıyan küçük bir tablo kurar.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3

import pytest

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parents[1]
ARAC = REPO / "research" / "olcumler" / "edg085_icra_ani_quote" / "rapor.py"


@pytest.fixture
def rapor():
    return betikten_modul_yukle(str(ARAC), "edg085_rapor_v466")


def _yaz(p: pathlib.Path, satirlar):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in satirlar),
                 encoding="utf-8")


def _quote(coid, sem, t, bid, ask, faz="pencere"):
    return {"tur": "quote", "alindi": t, "ts": t, "sembol": sem, "coid": coid, "faz": faz,
            "bid": bid, "ask": ask, "bid_lot": 1, "ask_lot": 1, "bx": "V", "ax": "V",
            "kosul": ["R"]}


def _ac(coid, sem, t, neden="new"):
    return {"tur": "pencere", "alindi": t, "sembol": sem, "coid": coid, "olay": "ac",
            "neden": neden}


def _dolum(coid, sem, t, yon, fiyat, son_quote, kayip=None, quote_n=1):
    return {"tur": "dolum", "alindi": t, "sembol": sem, "coid": coid, "yon": yon,
            "dolum_ts": t, "dolum_fiyat": fiyat, "dolum_fiyat_neden": None,
            "quote_n_pencere": quote_n, "son_quote": son_quote, "kayip_nedeni": kayip}


@pytest.fixture
def dunya(tmp_path):
    """Üç günlük sahte kayıt + E2 + trades + bars_intraday + taban/pilot taban.

    DÖRT DOLUM: 1 bant-içi (P-A) · 1 bant-dışı (P-B) · 1 quote'suz (P-C, `sembol_sessiz`) ·
    1 bracket çıkışı (uuid coid, bant-içi)."""
    kayit = tmp_path / "kayit"
    state = tmp_path / "state"
    (state / "intraday_bars").mkdir(parents=True)

    _yaz(kayit / "edg085_2026-09-21.jsonl", [
        _ac("P-A", "AAPL", "2026-09-21T14:00:00Z"),
        _quote("P-A", "AAPL", "2026-09-21T14:00:10Z", 100.00, 100.10),
        # FİYAT ASK + 1 TICK: bant-içiliği YALNIZ kartın ±1 tick payı sağlar. Payı kaldıran bir
        # mutasyon bu satırı bant-DIŞI yapar ve R2 ısırır (pay tam-eşitlikte sınanamaz).
        _dolum("P-A", "AAPL", "2026-09-21T14:00:20Z", "buy", 100.11,
               {"ts": "2026-09-21T14:00:10Z", "bid": 100.00, "ask": 100.10}),
    ])
    _yaz(kayit / "edg085_ham_2026-09-21.jsonl", [{"T": "q", "S": "AAPL", "bp": 100.0, "ap": 100.1}])
    _yaz(kayit / "edg085_2026-09-22.jsonl", [
        _ac("P-B", "MSFT", "2026-09-22T13:40:00Z"),
        _quote("P-B", "MSFT", "2026-09-22T13:40:05Z", 200.00, 200.10),
        _dolum("P-B", "MSFT", "2026-09-22T13:40:10Z", "buy", 200.50,
               {"ts": "2026-09-22T13:40:05Z", "bid": 200.00, "ask": 200.10}),
        _ac("P-C", "TSLA", "2026-09-22T14:59:50Z"),
        _dolum("P-C", "TSLA", "2026-09-22T15:00:00Z", "buy", 50.00, None,
               kayip="sembol_sessiz", quote_n=0),
    ])
    _yaz(kayit / "edg085_2026-09-23.jsonl", [
        _ac("e1a2-uuid", "AAPL", "2026-09-23T16:00:01Z", neden="fill_bracket"),
        _quote("e1a2-uuid", "AAPL", "2026-09-23T16:00:00Z", 105.00, 105.10, faz="halka_geri"),
        _dolum("e1a2-uuid", "AAPL", "2026-09-23T16:00:01Z", "sell", 105.00,
               {"ts": "2026-09-23T16:00:00Z", "bid": 105.00, "ask": 105.10}),
    ])

    _yaz(state / "entry_execution.jsonl", [
        {"ts": "2026-09-21T13:59:00Z", "plan_id": "P-A", "ticker": "AAPL", "karar": "submitted",
         "fill": 100.11},
        {"ts": "2026-09-22T13:39:00Z", "plan_id": "P-B", "ticker": "MSFT", "karar": "submitted",
         "fill": 200.50},
    ])
    _yaz(state / "intraday_bars" / "2026-09-21.jsonl", [
        {"ts": "2026-09-21T14:01:00Z",
         "bars": {"AAPL": {"o": 100.0, "h": 100.2, "l": 99.9, "c": 100.1, "v": 10,
                           "t": "2026-09-21T14:00:00Z"}}},
    ])

    con = sqlite3.connect(state / "meridian.db")
    con.execute("CREATE TABLE trades (seq INTEGER PRIMARY KEY, plan_id TEXT, entry REAL, "
                "extra_json TEXT)")
    con.execute("INSERT INTO trades (plan_id, entry, extra_json) VALUES (?,?,?)",
                ("P-A", 100.11, json.dumps({"alpaca_fill_price": 100.11,
                                            "dolum_ts": "2026-09-21T14:00:20Z"})))
    con.commit()
    con.close()

    taban = tmp_path / "taban.jsonl"
    _yaz(taban, [
        # ESKİ (cpu_kaynak YOK) = kart ADIM-0 (3) GEÇERSİZ ilanı → ELENMELİ ve SAYILMALI
        {"ts": "2026-09-08T13:30:00Z", "cpu_pct_tek_cekirdek": 0.00, "healthz_p50_ms": 1.5},
        {"ts": "2026-09-09T13:30:00Z", "cpu_pct_tek_cekirdek": 0.00, "healthz_p50_ms": 1.5},
        {"ts": "2026-09-14T13:30:00Z", "cpu_pct_tek_cekirdek": 4.0, "cpu_kaynak": "cgroup",
         "healthz_p50_ms": 1.5},
        {"ts": "2026-09-15T13:30:00Z", "cpu_pct_tek_cekirdek": 4.0, "cpu_kaynak": "cgroup",
         "healthz_p50_ms": 1.5},
        {"ts": "2026-09-16T13:30:00Z", "cpu_pct_tek_cekirdek": 4.0, "cpu_kaynak": "cgroup",
         "healthz_p50_ms": 1.5},
    ])
    pilot = tmp_path / "pilot.jsonl"
    _yaz(pilot, [
        {"ts": "2026-09-21T13:30:00Z", "cpu_pct_tek_cekirdek": 6.0, "cpu_kaynak": "cgroup",
         "healthz_p50_ms": 1.6},
        {"ts": "2026-09-22T13:30:00Z", "cpu_pct_tek_cekirdek": 6.0, "cpu_kaynak": "cgroup",
         "healthz_p50_ms": 1.6},
        {"ts": "2026-09-23T13:30:00Z", "cpu_pct_tek_cekirdek": 6.0, "cpu_kaynak": "cgroup",
         "healthz_p50_ms": 1.6},
    ])
    return {"kayit": kayit, "state": state, "taban": taban, "pilot": pilot, "kok": tmp_path}


def _argv(d, cikti, ek=()):
    return ["--kayit-dizin", str(d["kayit"]), "--state-dizin", str(d["state"]),
            "--baslangic", "2026-09-21", "--bitis", "2026-09-23",
            "--taban", str(d["taban"]), "--pilot-taban", str(d["pilot"]),
            "--cikti-dizin", str(cikti), *ek]


def _kos(rapor, d, tmp_path, ek=("--pk-sentetik",)):
    cikti = tmp_path / "cikti"
    rc = rapor.kos(_argv(d, cikti, ek))
    p = cikti / "sonuc_2026-09-23.json"
    return rc, (json.loads(p.read_text(encoding="utf-8")) if p.exists() else None), cikti


# =================================================================================================
# R1–R2 — K ölçüleri
# =================================================================================================
def test_R1_dolum_satirlari_ve_kayip_orani(rapor, dunya, tmp_path):
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert rc == 0
    assert s["n_dolum"] == 4 and s["n_seans"] == 3
    assert s["kayip_orani"] == 0.25
    assert s["kayip_nedenleri"] == {"sembol_sessiz": 1}


def test_R2_bant_ici_oran_ve_yon_farkindali_tani(rapor, dunya, tmp_path):
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert s["bant_paydasi_n"] == 3 and s["bant_ici_n"] == 2
    assert abs(s["bant_ici_oran"] - 2 / 3) < 1e-9
    t = s["tani_yon_farkindali_bps"]
    assert t["n"] == 3 and t["medyan"] is not None and t["p90"] is not None
    assert "acilis" in "".join(s["tani_sembol_saat"].keys()), "açılış kovası ayrı sayılmalı"


# =================================================================================================
# R3 — PK-1 sentetik
# =================================================================================================
def test_R3_pk1_sentetik_gecer(rapor, dunya, tmp_path):
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert s["pk"]["sentetik"]["hukum"] == "gecti", s["pk"]["sentetik"]
    assert rc == 0


def test_R3b_pk_kalinca_SAYI_YAYILMAZ_ve_cikis_2(rapor, dunya, tmp_path, monkeypatch):
    """KILL#7 çivisi: PK düşerse K ölçüleri None olur ve çıkış kodu 2'dir."""
    monkeypatch.setattr(rapor, "pk1_sentetik",
                        lambda tick: {"hukum": "kaldi", "olculen": {}, "beklenen": {}})
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert rc == 2
    assert s["kayip_orani"] is None and s["bant_ici_oran"] is None
    assert s["cpu_delta_pp"] is None and s["disk_mb_gun"] is None
    assert "kill#7" in s["yayin_neden"]


# =================================================================================================
# R4 — PK-3 bar çaprazı
# =================================================================================================
def test_R4_pk3_bar_caprazi_gecer_ve_bar_disina_cikinca_kalir(rapor, dunya, tmp_path):
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert s["pk"]["bar_capraz"]["hukum"] == "gecti" and s["pk"]["bar_capraz"]["sinanan_n"] == 1
    # barı quote bandının DIŞINA taşı → çapraz KALMALI
    _yaz(dunya["state"] / "intraday_bars" / "2026-09-21.jsonl", [
        {"ts": "2026-09-21T14:01:00Z",
         "bars": {"AAPL": {"o": 90.0, "h": 90.2, "l": 89.9, "c": 90.1,
                           "t": "2026-09-21T14:00:00Z"}}}])
    rc2, s2, _ = _kos(rapor, dunya, tmp_path)
    assert s2["pk"]["bar_capraz"]["hukum"] == "kaldi" and rc2 == 2


# =================================================================================================
# R5 — fizibilite deltası (eski taban satırları ELENİR ve SAYILIR)
# =================================================================================================
def test_R5_fizibilite_deltasi_ve_gecersiz_taban_elemesi(rapor, dunya, tmp_path):
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert s["cpu_taban_n_gecerli"] == 3 and s["cpu_taban_n_elenen"] == 2
    assert abs(s["cpu_delta_pp"] - 2.0) < 1e-9, "medyan(pilot cgroup) − medyan(taban cgroup)"
    assert s["healthz_p95_delta_ms"] is not None
    assert s["disk_mb_gun"] is not None and s["disk_mb_gun"] > 0


# =================================================================================================
# R6 — örneklem kapısı
# =================================================================================================
def test_R6_orneklem_kapisi_hukum_YOK_ama_sayilar_yazilir(rapor, dunya, tmp_path):
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert s["hukum"] is None and "örneklem kapısı" in s["hukum_neden"]
    assert s["n_dolum"] == 4 and s["kayip_orani"] == 0.25, "betimleyici sayılar YİNE yazılır"


# =================================================================================================
# R7 — eşlenemeyen dolum ADIYLA
# =================================================================================================
def test_R7_eslenemeyen_dolum_ADIYLA_sayilir(rapor, dunya, tmp_path):
    rc, s, _ = _kos(rapor, dunya, tmp_path)
    assert s["eslenemeyen"] == ["P-C"], "E2'de plan_id'si olmayan motor dolumu adıyla düşmeli"
    assert s["bracket_bacagi"] == ["e1a2-uuid"], "bracket bacağı E2'de aranmaz, AYRI sayılır"


# =================================================================================================
# R8 — salt-okurluk
# =================================================================================================
def test_R8_state_dizinine_YAZILMAZ(rapor, dunya, tmp_path):
    once = sorted((str(p), p.stat().st_size) for p in dunya["state"].rglob("*"))
    _kos(rapor, dunya, tmp_path)
    sonra = sorted((str(p), p.stat().st_size) for p in dunya["state"].rglob("*"))
    assert once == sonra, "rapor aracı state dizinine dokundu"


# =================================================================================================
# R9 — sonuc.json alan sözleşmesi + eşiklerin karttan gelmesi
# =================================================================================================
def test_R9_sonuc_alanlari_ve_esikler(rapor, dunya, tmp_path):
    rc, s, cikti = _kos(rapor, dunya, tmp_path)
    for alan in ("pencere", "n_dolum", "n_seans", "kayip_orani", "kayip_nedenleri",
                 "bant_ici_oran", "bant_ici_n", "tani_yon_farkindali_bps", "tani_sembol_saat",
                 "disk_mb_gun", "cpu_delta_pp", "healthz_p95_delta_ms", "pk", "esikler",
                 "hukum", "uretim_utc", "girdi_sha256", "eslenemeyen", "cpu_taban_n_gecerli"):
        assert alan in s, f"sonuc.json alanı eksik: {alan}"
    assert s["esikler"]["kayip_orani_ust"] == 0.30
    assert s["esikler"]["tutarlilik_bant_ici_oran_alt"] == 0.95
    assert s["esikler"]["disk_gun_basi_mb_ust"] == 50
    assert s["esikler"]["cpu_payi_delta_ust_pp"] == 5
    assert s["esikler"]["healthz_p95_delta_ms_ust"] == 50
    assert s["pk"]["gercek"]["hukum"] is None and "elle" in s["pk"]["gercek"]["neden"]
    assert set(s["girdi_sha256"]) >= {"edg085_2026-09-21.jsonl", "edg085_ham_2026-09-21.jsonl"}
    md = (cikti / "rapor_2026-09-23.md").read_text(encoding="utf-8")
    assert "IEX temsiliyeti" in md, "kill#5 satırı karttan AYNEN rapora girmeli"


def test_R10_kayit_dizini_yoksa_cikis_1(rapor, tmp_path):
    rc = rapor.kos(["--kayit-dizin", str(tmp_path / "yok"), "--state-dizin", str(tmp_path),
                    "--baslangic", "2026-09-21", "--bitis", "2026-09-23",
                    "--cikti-dizin", str(tmp_path / "c")])
    assert rc == 1


def test_R11_OPERATORUN_KOSACAGI_BICIMDE_modul_olarak_calisir(rapor, dunya, tmp_path,
                                                              monkeypatch):
    """CLAUDE.md §6: araç, operatörün koşacağı BİÇİMDE bir kez koşulmadan teslim edilmez
    (18 çivi yeşilken `--uygula` sessizce yok sayılıyordu vakası). Burada `runpy` ile
    `python -m research.olcumler.edg085_icra_ani_quote.rapor` yolunun ta kendisi koşar —
    `__main__` dalı, argparse ve `sys.exit` sözleşmesi dâhil (alt süreç YOK: ajan kapsamında
    pytest dışı koşum yasak, `runpy` aynı yolu süreç doğurmadan yürütür)."""
    import runpy
    cikti = tmp_path / "cikti_modul"
    monkeypatch.setattr("sys.argv", ["rapor", *_argv(dunya, cikti, ("--pk-sentetik",))])
    with pytest.raises(SystemExit) as ex:
        runpy.run_module("research.olcumler.edg085_icra_ani_quote.rapor", run_name="__main__")
    assert ex.value.code == 0
    assert (cikti / "sonuc_2026-09-23.json").exists()
    assert (cikti / "rapor_2026-09-23.md").exists()

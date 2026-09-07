"""tests/test_tohum_pit_yenile_v433.py — `ops/tohum_pit_yenile.py` çivisi (TSK-159 S5, 2026-09-07).

NE ÖLÇER. Plan `docs/superpowers/plans/2026-09-07-s5-tohum-pit.md` Task 1: canlı `trades`/
`trade_plans` defterindeki TOHUM dilimini PIT üyelikli (varyant A) yeni bir tohumla değiştiren
ops betiğinin (a) kuru koşumda `state/` ve yedek dizinine TEK BAYT yazmadığını, (b) canlı worker
nabzı tazeyken / silahlı plan varken `--uygula`yı REDDETTİĞİNİ, (c) `--uygula`da CANLI satırları
BİT-AYNI koruduğunu, eski tohumu ARŞİVLEDİĞİNİ, yeni satırları sözleşmeli damgalarla yazdığını,
`llm_opinion` damgalı planı KORUDUĞUNU, eğri `points`ine DOKUNMADIĞINI ve reset işaretini
eklediğini, (d) `ledgerstamp.seed_boundary()`nin yeni tohumun max `ts_close`unu ölçtüğünü,
(e) rapor şemasının okunabilir olduğunu kanıtlar.

AĞSIZ, OBS'SUZ: her motor/defter dokunuşu `sandbox_state` altındadır (`config.STATE` tmp'e döner),
`backtest.replay` ve `dataset.load` SAHTELENİR — bu dosya ne ağa çıkar ne canlı `state/`e yazar.
Yedek dizini de `--yedek-dizin` ile tmp'ye yönlendirilir: depo `backups/` dizinine HİÇBİR test
yazmaz.

MUTASYON KANITLARI (CLAUDE.md §6 — yeşil kanıt değildir):
  MUTASYON 1 (canlı satır koruma dalı): `defter_ayir` içindeki `!=` `==` yapılırsa (yani "tohum
  olmayan satırı koru" yerine "tohum satırını koru") canlı/belirsiz satırlar defterden düşer —
  `test_MUTASYON1_korunan_dal_ters_cevrilirse_canli_satir_kaybolur` bu dalın ISIRDIĞINI aynı
  fonksiyonu TERS mantıkla çağırarak gösterir; uçtan-uca karşılığı
  `test_uygula_canli_satirlar_bit_ayni_korunur`dur.
  MUTASYON 2 (arşiv yazımı): `arsiv_yaz` çağrılmazsa/boş liste yazarsa arşiv dosyasının satır
  sayısı ve sha256'sı eski tohumla eşleşmez — `test_MUTASYON2_arsiv_bos_yazilirsa_sha_tutmaz`
  arşiv doğrulamasının (n + sha256) ISIRDIĞINI gösterir.

KAPSAM DIŞI: hüküm (Rol-1 verir; betikte EŞİK YOK), `backtest.replay`in `uyelik` süzgecinin
kendi doğruluğu (`tests/test_replay_uyelik_suzgeci_v427.py`), EDG-082 ölçüm betiğinin kendi
doğruluğu (`tests/test_edg082_olcum_v428.py`)."""
from __future__ import annotations

import hashlib
import json
import pathlib

import pandas as pd
import pytest

from meridian import backtest, config, ledgerstamp, sermaye, store
from tests.conftest import betikten_modul_yukle, make_bars

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK / "ops" / "tohum_pit_yenile.py"
KART036 = KOK / "research" / "cards" / "EDG-2026-036-tohum-yenileme.yaml"


def _betik():
    return betikten_modul_yukle(BETIK, "tohum_pit_yenile")


# =================================================================================================
# SAHNE — sandbox defteri + donuk üyelik girdileri + SAHTE replay
# =================================================================================================

ESKI_PARTI = "EDG-036b-2026-08-13"

ESKI_TOHUM = [
    {"id": "T00001", "ts_open": "2023-05-02", "ts_close": "2023-05-19", "ticker": "MEM",
     "side": "long", "entry": 10.0, "exit": 11.0, "qty": 10, "r_multiple": 1.0,
     "pnl_dollars": 10.0, "exit_reason": "target", "strategy_version": 90,
     "plan_id": "P-2023-05-01-MEM", "kaynak": "replay_seed", "tohum_parti": ESKI_PARTI},
    {"id": "T00002", "ts_open": "2024-02-01", "ts_close": "2026-07-24", "ticker": "EQR",
     "side": "long", "entry": 20.0, "exit": 19.0, "qty": 5, "r_multiple": -1.0,
     "pnl_dollars": -5.0, "exit_reason": "stop", "strategy_version": 90,
     "plan_id": "P-2024-02-01-EQR", "kaynak": "replay_seed", "tohum_parti": ESKI_PARTI},
]
CANLI = [
    {"id": "T00096", "ts_open": "2026-08-19", "ts_close": "2026-08-20", "ticker": "AAA",
     "side": "long", "entry": 30.0, "exit": 31.5, "qty": 3, "r_multiple": 0.5,
     "pnl_dollars": 4.5, "exit_reason": "target", "strategy_version": 5,
     "plan_id": "P-2026-08-19-AAA", "kaynak": "live_paper"},
    {"id": "T00097", "ts_open": "2026-08-31", "ts_close": "2026-09-01", "ticker": "MEM",
     "side": "long", "entry": 12.0, "exit": 11.4, "qty": 2, "r_multiple": -0.4,
     "pnl_dollars": -1.2, "exit_reason": "stop", "strategy_version": 5,
     "plan_id": "P-2026-08-31-MEM", "kaynak": "live_paper"},
]
BELIRSIZ = [
    {"id": "T00098", "ts_open": "2026-08-24", "ts_close": "2026-08-25", "ticker": "AAA",
     "side": "long", "entry": 33.0, "exit": 33.0, "qty": 1, "r_multiple": 0.0,
     "pnl_dollars": 0.0, "exit_reason": "time_stop", "strategy_version": 5,
     "plan_id": "P-2026-08-24-AAA"},
]
PLANLAR = [
    {"id": "P-2023-05-01-MEM", "date": "2023-05-01", "ticker": "MEM", "gate_verdict": "GO",
     "strategy_version": 90},
    {"id": "P-2024-02-01-EQR", "date": "2024-02-01", "ticker": "EQR", "gate_verdict": "GO",
     "strategy_version": 90},
    {"id": "P-2026-08-19-AAA", "date": "2026-08-19", "ticker": "AAA", "gate_verdict": "GO",
     "strategy_version": 5, "llm_opinion": {"verdict": "GO", "conf": 0.7}},
    {"id": "P-2026-08-31-MEM", "date": "2026-08-31", "ticker": "MEM", "gate_verdict": "REVIEW",
     "strategy_version": 5},
    {"id": "P-2026-09-02-CCC", "date": "2026-09-02", "ticker": "CCC", "gate_verdict": "NO_GO",
     "strategy_version": 5},
]
REALIZED = 277.98314200393065
EGRI = {"version": 5, "points": [["2026-07-18", 94000.0], ["2026-07-20", 94457.91]],
        sermaye.CURVE_MARK_KEY: [
            {"id": "SR-20260801", "tarih": "2026-08-01T00:00:00+00:00",
             "tip": "paper_equity_reset", "egri_son_nokta": ["2026-07-20", 94457.91]}]}

# SAHTE replay'in ürettiği ÜÇ işlem — hepsi güncel listede olan sembollerde (sızıntı 0 beklenir).
SAHTE_TRADES = [
    {"id": "T00001", "ts_open": "2022-03-01", "ts_close": "2022-03-15", "ticker": "MEM",
     "side": "long", "entry": 9.0, "exit": 10.0, "qty": 11, "r_multiple": 1.1,
     "pnl_dollars": 11.0, "exit_reason": "target", "strategy_version": 5,
     "plan_id": "P-2022-02-28-MEM"},
    {"id": "T00002", "ts_open": "2023-06-01", "ts_close": "2023-06-09", "ticker": "EQR",
     "side": "long", "entry": 21.0, "exit": 20.0, "qty": 4, "r_multiple": -0.8,
     "pnl_dollars": -4.0, "exit_reason": "stop", "strategy_version": 5,
     "plan_id": "P-2023-05-31-EQR"},
    {"id": "T00003", "ts_open": "2026-08-10", "ts_close": "2026-08-28", "ticker": "AAA",
     "side": "long", "entry": 30.0, "exit": 33.0, "qty": 6, "r_multiple": 2.0,
     "pnl_dollars": 18.0, "exit_reason": "target", "strategy_version": 5,
     "plan_id": "P-2026-08-19-AAA"},          # CANLI planla ÇAKIŞAN kimlik (bilerek)
]
SAHTE_PLANLAR = [
    {"id": "P-2022-02-28-MEM", "date": "2022-02-28", "ticker": "MEM", "gate_verdict": "GO",
     "gate_checks": [{"check": "x", "passed": True}]},
    {"id": "P-2023-05-31-EQR", "date": "2023-05-31", "ticker": "EQR", "gate_verdict": "GO",
     "gate_checks": [{"check": "x", "passed": True}]},
    {"id": "P-2026-08-19-AAA", "date": "2026-08-19", "ticker": "AAA", "gate_verdict": "GO",
     "gate_checks": [{"check": "x", "passed": True}]},
]


def _sha(rows: list[dict]) -> str:
    return hashlib.sha256(
        "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
        .encode("utf-8")).hexdigest()


def _durum(kok: pathlib.Path) -> dict:
    """Bir dizin ağacının (yol → (sha256, boyut)) fotoğrafı — 'tek bayt yazmadı' ölçümü."""
    out = {}
    for p in sorted(pathlib.Path(kok).rglob("*")):
        if p.is_file():
            ham = p.read_bytes()
            out[str(p.relative_to(kok))] = (hashlib.sha256(ham).hexdigest(), len(ham))
    return out


@pytest.fixture
def sahne(sandbox_state, tmp_path, monkeypatch):
    """Defteri kurar, üyelik girdilerini (donuk HTML + güncel liste) yazar, `dataset.load` ve
    `backtest.replay`i SAHTELER. Nabız DOSYASI YOK → `health.stale` fail-closed True döner, yani
    varsayılan sahnede worker DURMUŞ sayılır ve `--uygula` KAPI-0'dan geçer."""
    store.write_jsonl("trades.jsonl", ESKI_TOHUM + CANLI + BELIRSIZ)
    store.write_jsonl("trade_plans.jsonl", PLANLAR)
    store.write_json("portfolio.json", {"cash": 100000.0, "realized_pnl": REALIZED, "armed": []})
    store.write_json("equity_curve.json", EGRI)
    # CANLI PARAMETRE SETİ ŞART: betik `strategy.yaml` YOKSA reddeder (varsayılanlarla tohum
    # üretmek, tohumun "yürürlükteki paketi temsil eder" beyanını sessizce yalanlardı).
    config.dump_yaml(config.default_strategy(), config.strategy_path())

    html = ('<table><tr><th>Effective Date</th><th>Added</th><th>Removed</th><th>Reason</th></tr>'
            '<tr><td>2021-01-04</td><td>MEM</td><td></td><td>v433-test-join</td></tr></table>')
    html_yolu = tmp_path / "degisiklikler.html"
    html_yolu.write_text(html, encoding="utf-8")
    guncel_yolu = tmp_path / "guncel.json"
    guncel_yolu.write_text(json.dumps(["VMRK", "AAA", "MEM"]), encoding="utf-8")

    idx = make_bars(120, seed=7, trend=0.0004)
    bars = {"MEM": make_bars(120, seed=2), "EQR": make_bars(120, seed=3),
            "AAA": make_bars(120, seed=11)}
    from meridian import dataset as dataset_mod
    monkeypatch.setattr(dataset_mod, "load", lambda *a, **k: (bars, idx))

    cagrilar: list = []

    def _sahte_replay(params, b, index_bars, goal, start, end, **kw):
        cagrilar.append({"start": start, "end": end, **kw})
        return backtest.BacktestResult(
            trades=[dict(t) for t in SAHTE_TRADES],
            equity=[("2022-01-03", 100000.0), ("2026-09-05", 120000.0)],
            params=params, start=start, end=end,
            plan_log=[dict(p) for p in SAHTE_PLANLAR], candidate_log=[])

    monkeypatch.setattr(backtest, "replay", _sahte_replay)

    yedek = tmp_path / "yedekler"
    rapor = tmp_path / "rapor"
    return {"html": html_yolu, "guncel": guncel_yolu, "yedek": yedek, "rapor": rapor,
            "cagrilar": cagrilar, "state": sandbox_state, "idx": idx}


def _argv(sahne, *ek) -> list[str]:
    return ["--girdi-html", str(sahne["html"]), "--guncel-liste", str(sahne["guncel"]),
            "--baslangic", "2022-01-01", "--bitis", "2026-09-05",
            "--yedek-dizin", str(sahne["yedek"]), "--kapi-atla", *ek]


def _rapor_oku(sahne) -> dict:
    return json.loads((sahne["rapor"] / "rapor.json").read_text(encoding="utf-8"))


# =================================================================================================
# (a) KURU KOŞUM — TEK BAYT YAZMAZ
# =================================================================================================

def test_kuru_kosum_rapor_dizinsiz_hicbir_bayt_yazmaz(sahne):
    """`--rapor-dizin` VERİLMEZSE kuru koşum hiçbir dosyaya dokunmaz — rapor yalnız stdout'a."""
    b = _betik()
    once_state, once_yedek = _durum(sahne["state"]), _durum(sahne["yedek"].parent)
    rc = b.ana(_argv(sahne))
    assert rc == 0
    assert _durum(sahne["state"]) == once_state
    assert _durum(sahne["yedek"].parent) == once_yedek
    assert not sahne["yedek"].exists()


def test_kuru_kosum_rapor_dizini_verilince_YALNIZ_raporu_yazar(sahne):
    b = _betik()
    once_state = _durum(sahne["state"])
    rc = b.ana(_argv(sahne, "--rapor-dizin", str(sahne["rapor"])))
    assert rc == 0
    assert _durum(sahne["state"]) == once_state, "kuru koşum state/'e YAZDI"
    assert not sahne["yedek"].exists(), "kuru koşum yedek dizinini KURDU"
    r = _rapor_oku(sahne)
    assert r["mod"] == "kuru"
    assert r["yazim"]["calisti"] is False


def test_kuru_kosum_defter_ozetini_onceki_blogunda_verir(sahne):
    b = _betik()
    b.ana(_argv(sahne, "--rapor-dizin", str(sahne["rapor"])))
    onceki = _rapor_oku(sahne)["onceki"]
    assert onceki["trades"]["replay_seed_n"] == len(ESKI_TOHUM)
    assert onceki["trades"]["live_paper_n"] == len(CANLI)
    assert onceki["trades"]["belirsiz_n"] == len(BELIRSIZ)
    assert onceki["trade_plans"]["toplam"] == len(PLANLAR)
    assert onceki["trade_plans"]["llm_opinion_n"] == 1
    assert onceki["portfolio"]["realized_pnl"] == REALIZED
    assert onceki["equity"]["n_nokta"] == len(EGRI["points"])


# =================================================================================================
# (b) KAPI-0 — nabız taze / silahlı plan
# =================================================================================================

def test_nabiz_tazeyse_uygula_reddedilir_ve_defter_degismez(sahne):
    from meridian import health, memory
    store.write_json("heartbeat.json", {"ts": memory.now_iso()})
    assert health.stale(900) is False, "sahne kurulumu: nabız TAZE olmalıydı"
    b = _betik()
    once = _durum(sahne["state"])
    rc = b.ana(_argv(sahne, "--uygula", "--rapor-dizin", str(sahne["rapor"])))
    assert rc != 0
    assert _durum(sahne["state"]) == once
    k = _rapor_oku(sahne)["kapi_0"]
    assert k["uygula_izni"] is False
    assert k["nabiz_bayat"] is False


def test_silahli_plan_varsa_uygula_reddedilir(sahne):
    store.write_json("portfolio.json", {"cash": 1.0, "realized_pnl": REALIZED,
                                        "armed": [{"ticker": "AAA"}]})
    b = _betik()
    once = _durum(sahne["state"])
    rc = b.ana(_argv(sahne, "--uygula", "--rapor-dizin", str(sahne["rapor"])))
    assert rc != 0
    assert _durum(sahne["state"]) == once
    k = _rapor_oku(sahne)["kapi_0"]
    assert k["uygula_izni"] is False and k["armed_n"] == 1


def test_nabiz_taze_olsa_bile_KURU_kosum_serbest(sahne):
    from meridian import memory
    store.write_json("heartbeat.json", {"ts": memory.now_iso()})
    b = _betik()
    rc = b.ana(_argv(sahne, "--rapor-dizin", str(sahne["rapor"])))
    assert rc == 0
    assert _rapor_oku(sahne)["kapi_0"]["uygula_izni"] is False


def test_uygula_rapor_dizinsiz_kullanim_hatasi(sahne):
    b = _betik()
    once = _durum(sahne["state"])
    rc = b.ana(_argv(sahne, "--uygula"))
    assert rc == 2, "yazan koşum RAPORSUZ (Yasa 6 okuyucusuz) kabul edilmemeliydi"
    assert _durum(sahne["state"]) == once


# =================================================================================================
# (c) --uygula — bütünlük, arşiv, damgalar, plan koruma, eğri
# =================================================================================================

@pytest.fixture
def uygulandi(sahne):
    b = _betik()
    rc = b.ana(_argv(sahne, "--uygula", "--rapor-dizin", str(sahne["rapor"])))
    assert rc == 0, "uygulama düştü"
    return {"betik": b, "sahne": sahne, "rapor": _rapor_oku(sahne)}


def test_uygula_canli_satirlar_bit_ayni_korunur(uygulandi):
    rows = store.read_jsonl("trades.jsonl")
    korunan = [r for r in rows if ledgerstamp.kaynak_of(r) != ledgerstamp.REPLAY_SEED]
    assert _sha(korunan) == _sha(CANLI + BELIRSIZ), "canlı/belirsiz satırlar BİT-AYNI değil"
    assert store.read_json("portfolio.json")["realized_pnl"] == REALIZED


def test_uygula_eski_tohum_defterden_dustu_yeni_tohum_girdi(uygulandi):
    rows = store.read_jsonl("trades.jsonl")
    tohum = [r for r in rows if ledgerstamp.kaynak_of(r) == ledgerstamp.REPLAY_SEED]
    assert len(tohum) == len(SAHTE_TRADES)
    assert all(r.get("tohum_parti") == uygulandi["betik"].TOHUM_PARTI for r in tohum)
    assert not any(r.get("tohum_parti") == ESKI_PARTI for r in rows)
    assert len(rows) == len(SAHTE_TRADES) + len(CANLI) + len(BELIRSIZ)


def test_uygula_yeni_tohum_damgalari_sozlesmeli(uygulandi):
    b = uygulandi["betik"]
    tohum = [r for r in store.read_jsonl("trades.jsonl")
             if ledgerstamp.kaynak_of(r) == ledgerstamp.REPLAY_SEED]
    serh = b.friksiyon_serhi_oku(KART036)
    for r in tohum:
        assert r["kaynak"] == ledgerstamp.REPLAY_SEED     # ruling 1: yeni kaynak değeri YOK
        assert r["strategy_version"] == b.TOHUM_SURUM == 91
        assert r["pit_uyelik"] == "as_of" and r["varyant"] == "A"
        assert r["tohum_parti"] == b.TOHUM_PARTI
        assert len(r["params_sha256"]) == 64 and len(r["guncel_liste_sha256"]) == 64
        assert "motor_kunye" in r
        assert r["friksiyon_serhi"] == serh


def test_uygula_arsiv_eski_tohumu_tasir_ve_sha_dosyasi_var(uygulandi):
    rapor = uygulandi["rapor"]
    arsiv = pathlib.Path(rapor["yazim"]["arsiv_yolu"])
    sha_yolu = pathlib.Path(rapor["yazim"]["arsiv_sha_yolu"])
    assert arsiv.exists() and sha_yolu.exists()
    ham = arsiv.read_bytes()
    assert hashlib.sha256(ham).hexdigest() == rapor["yazim"]["arsiv_sha256"]
    assert sha_yolu.read_text(encoding="utf-8").split()[0] == rapor["yazim"]["arsiv_sha256"]
    satirlar = [json.loads(s) for s in ham.decode("utf-8").splitlines() if s.strip()]
    trades = [s["satir"] for s in satirlar if s["defter"] == "trades.jsonl"]
    planlar = [s["satir"] for s in satirlar if s["defter"] == "trade_plans.jsonl"]
    assert _sha(trades) == _sha(ESKI_TOHUM), "arşivlenen tohum satırları BİT-AYNI değil"
    assert {p["id"] for p in planlar} == {"P-2023-05-01-MEM", "P-2024-02-01-EQR"}


def test_uygula_llm_opinion_plani_ve_canli_planlar_korunur(uygulandi):
    planlar = store.read_jsonl("trade_plans.jsonl")
    ids = [p["id"] for p in planlar]
    # llm_opinion damgalı plan BİT-AYNI korunur (aynı kimlikte tohum planı da vardı — canlı KAZANIR)
    korunan = [p for p in planlar if p["id"] == "P-2026-08-19-AAA"]
    assert len(korunan) == 1
    assert json.dumps(korunan[0], sort_keys=True) == json.dumps(PLANLAR[2], sort_keys=True)
    assert "P-2026-08-31-MEM" in ids and "P-2026-09-02-CCC" in ids
    assert "P-2023-05-01-MEM" not in ids and "P-2024-02-01-EQR" not in ids
    assert "P-2022-02-28-MEM" in ids and "P-2023-05-31-EQR" in ids


def test_uygula_plan_kimlik_cakismasi_olculur_ve_raporlanir(uygulandi):
    y = uygulandi["rapor"]["yazim"]["trade_plans"]
    assert y["cakisan_kimlik_n"] == 1
    assert y["cakisan_kimlikler"] == ["P-2026-08-19-AAA"]


def test_uygula_egri_noktalari_dokunulmaz_reset_isareti_eklenir(uygulandi):
    b = uygulandi["betik"]
    eq = store.read_json("equity_curve.json")
    assert eq["points"] == EGRI["points"], "`points` DEĞİŞTİ"
    isaretler = sermaye._egri_isaretleri(eq)
    assert len(isaretler) == len(EGRI[sermaye.CURVE_MARK_KEY]) + 1
    yeni = isaretler[-1]
    assert yeni["tur"] == "tohum_degisimi"
    assert yeni["tohum_parti"] == b.TOHUM_PARTI
    assert yeni["onceki_n"] == len(ESKI_TOHUM) and yeni["yeni_n"] == len(SAHTE_TRADES)
    assert "ts" in yeni and yeni.get("id")


def test_uygula_scoreboard_ve_candidates_dokunulmaz(sahne):
    store.write_json("scoreboard.json", {"current_version": 5, "versions": {"5": {"live_score": 1}}})
    store.write_jsonl("candidates.jsonl", [{"date": "2026-09-01", "ticker": "AAA"}])
    once_sb = store.stamp("scoreboard.json")
    once_cd = store.stamp("candidates.jsonl")
    b = _betik()
    assert b.ana(_argv(sahne, "--uygula", "--rapor-dizin", str(sahne["rapor"]))) == 0
    assert store.stamp("scoreboard.json") == once_sb
    assert store.stamp("candidates.jsonl") == once_cd


# =================================================================================================
# (d) SEED BOUNDARY — yeni tohumun max ts_close'u
# =================================================================================================

def test_uygula_sonrasi_seed_boundary_yeni_max_ts_close(uygulandi):
    sinir = ledgerstamp.seed_boundary()
    beklenen = max(t["ts_close"] for t in SAHTE_TRADES)[:10]
    assert sinir["replay_end"] == beklenen
    assert sinir["kaynak"] == ledgerstamp.KAYNAK_DAMGA
    assert uygulandi["rapor"]["dogrulama"]["seed_boundary"]["replay_end"] == beklenen


def test_uygula_sonrasi_belirsiz_sayaci_degismedi(uygulandi):
    sayac = ledgerstamp.counts()
    assert sayac["replay_seed_n"] == len(SAHTE_TRADES)
    assert sayac["live_paper_n"] == len(CANLI)
    assert sayac["belirsiz_n"] == len(BELIRSIZ)
    assert uygulandi["rapor"]["dogrulama"]["counts"]["belirsiz_n"] == len(BELIRSIZ)


# =================================================================================================
# (e) RAPOR ŞEMASI + kıyas + sızıntı + damga tek-kaynağı
# =================================================================================================

def test_rapor_semasi_zorunlu_bloklari_tasir(sahne):
    b = _betik()
    b.ana(_argv(sahne, "--rapor-dizin", str(sahne["rapor"])))
    r = _rapor_oku(sahne)
    for blok in ("arac", "mod", "zaman", "sozlesme", "kapi_0", "girdi_kimligi", "onceki",
                 "replay", "kiyas", "yazim", "dogrulama", "beyan", "acik_sorular"):
        assert blok in r, f"rapor bloğu eksik: {blok}"
    assert (sahne["rapor"] / "rapor.md").exists()
    g = r["girdi_kimligi"]
    assert len(g["html_sha256"]) == 64 and len(g["guncel_liste_sha256"]) == 64
    assert g["baslangic"] == "2022-01-01" and g["bitis"] == "2026-09-05"
    assert g["tohum_strateji_surumu"] == 91


def test_kiyas_yil_bazinda_ve_cikis_nedeni_dagilimi(sahne):
    b = _betik()
    b.ana(_argv(sahne, "--rapor-dizin", str(sahne["rapor"])))
    k = _rapor_oku(sahne)["kiyas"]
    assert k["eski_tohum"]["n"] == len(ESKI_TOHUM) and k["yeni_tohum"]["n"] == len(SAHTE_TRADES)
    assert k["delta"]["n"] == len(SAHTE_TRADES) - len(ESKI_TOHUM)
    assert k["yeni_tohum"]["yil_bazinda"] == {"2022": 1, "2023": 1, "2026": 1}
    assert k["yeni_tohum"]["cikis_nedeni"] == {"stop": 1, "target": 2}
    assert k["sizinti"]["n_uye_olmayan"] == 0
    assert k["sizinti"]["n_hic_uye"] == 0


def test_sizinti_uye_olmayan_sembolu_sayar(sahne, monkeypatch):
    """Sızıntı ölçümü KÖR DEĞİL: güncel listede olmayan bir sembolde işlem üretilirse SAYILIR."""
    sizan = [dict(SAHTE_TRADES[0], ticker="ZZZ")]

    def _replay(params, b_, idx, goal, start, end, **kw):
        return backtest.BacktestResult(trades=[dict(t) for t in sizan], equity=[],
                                       params=params, start=start, end=end,
                                       plan_log=[], candidate_log=[])

    monkeypatch.setattr(backtest, "replay", _replay)
    b = _betik()
    b.ana(_argv(sahne, "--rapor-dizin", str(sahne["rapor"])))
    assert _rapor_oku(sahne)["kiyas"]["sizinti"]["n_uye_olmayan"] == 1


def test_friksiyon_serhi_karttan_okunur_uydurulmaz(tmp_path):
    b = _betik()
    serh = b.friksiyon_serhi_oku(KART036)
    assert "slippage_bps=5" in serh and "gerçekleşen İCRAYI DEĞİL" in serh
    bozuk = tmp_path / "kart.yaml"
    bozuk.write_text("card_id: X\nasama1_hukmu: {DAMGA_KARARI: 'serh yok'}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="FRİKSİYON"):
        b.friksiyon_serhi_oku(bozuk)


def test_replay_A_uyelik_fonksiyonu_ve_sv91_ile_cagrilir(sahne):
    b = _betik()
    b.ana(_argv(sahne, "--rapor-dizin", str(sahne["rapor"])))
    assert len(sahne["cagrilar"]) == 1
    c = sahne["cagrilar"][0]
    assert c["strategy_version"] == 91
    assert c["with_gate_detail"] is True
    assert callable(c["uyelik"]), "varyant A üyelik fonksiyonu GEÇİRİLMEDİ"
    assert c["uyelik"]("2022-06-01") == {"VMRK", "AAA", "MEM"} or "EQR" in c["uyelik"]("2022-06-01")


# =================================================================================================
# MUTASYONLAR — yeşilin NEDEN yeşil olduğunu gösterir
# =================================================================================================

def test_MUTASYON1_korunan_dal_ters_cevrilirse_canli_satir_kaybolur(sahne):
    """`defter_ayir` "tohum OLMAYAN satırı koru" der. Karşılaştırma TERS çevrilirse (mutasyon)
    korunan kümesi tohum satırlarına döner ve canlı satırlar defterden düşerdi."""
    b = _betik()
    rows = ESKI_TOHUM + CANLI + BELIRSIZ
    dogru = b.defter_ayir(rows)
    assert _sha(dogru["korunan"]) == _sha(CANLI + BELIRSIZ)
    assert _sha(dogru["tohum"]) == _sha(ESKI_TOHUM)
    mutant = [r for r in rows if ledgerstamp.kaynak_of(r) == ledgerstamp.REPLAY_SEED]
    assert _sha(mutant) != _sha(dogru["korunan"]), "mutasyon ISIRMADI"
    assert not any(r in mutant for r in CANLI)


def test_MUTASYON2_arsiv_bos_yazilirsa_sha_tutmaz(uygulandi, tmp_path):
    """Arşiv doğrulaması (satır sayısı + sha256) gerçekten ısırıyor mu: aynı yolu BOŞ içerikle
    yeniden yazınca raporun sha256'sı artık dosyayla uyuşmaz."""
    rapor = uygulandi["rapor"]
    arsiv = pathlib.Path(rapor["yazim"]["arsiv_yolu"])
    beklenen = rapor["yazim"]["arsiv_sha256"]
    assert hashlib.sha256(arsiv.read_bytes()).hexdigest() == beklenen
    arsiv.write_text("", encoding="utf-8")
    assert hashlib.sha256(arsiv.read_bytes()).hexdigest() != beklenen
    assert rapor["yazim"]["arsiv_n_trades"] == len(ESKI_TOHUM)


def test_MUTASYON2b_arsiv_yazilmadan_uygulama_yapilmaz(sahne, monkeypatch):
    """Arşiv yazımı DÜŞERSE defter DEĞİŞMEZ — 'arşivle, sonra değiştir' sırası ısırıyor mu."""
    b = _betik()
    once = _durum(sahne["state"])

    def _patla(*a, **k):
        raise OSError("v433: arşiv yazımı bilerek düşürüldü")

    monkeypatch.setattr(b, "arsiv_yaz", _patla)
    rc = b.ana(_argv(sahne, "--uygula", "--rapor-dizin", str(sahne["rapor"])))
    assert rc != 0
    assert _durum(sahne["state"]) == once, "arşiv düşmesine rağmen defter DEĞİŞTİ"

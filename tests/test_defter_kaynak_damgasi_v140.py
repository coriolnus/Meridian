"""test_defter_kaynak_damgasi_v140.py — BT-1 (defter kaynak damgası) + AT-1 (alfa/beta kablosu).

BU TURUN ORTAK SINIFI: **ölçümün ZEMİNİ ölçülmemişti.**

  BT-1. `state/trades.jsonl` iki yazardan besleniyor — canlı kâğıt döngü (`loop._persist_trade`,
        append) ve replay tohumu (`run.replay_seed`, defterin TAMAMINI tek toplu yazımla ezer).
        Satırlarda kaynak damgası yoktu, dolayısıyla `learning_scorecard`, skor kalibrasyonu ve
        her atribüsyon ölçümü 95 satırın tamamını "canlı defter" sanıyordu. Gerçek canlı n
        HİÇBİR YERDE yazmıyordu ve bugünkü ölçümle 0'dır.

  AT-1. Dört dolar ölçütü "para kazandık mı?" diye sorar; hiçbiri "kazandıysak bu piyasa mıydı?"
        diye sormaz. İşlem-penceresi alfa/beta 2026-07-30 gecesi ELLE ölçüldü ve hiçbir yere
        kablolanmadı. Bu tur onu kalıcı hâle getirir — ADVISORY, dört ölçütü DEĞİŞTİRMEZ.

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` üzerinden koşar. SPY barları SENTETİK ve
DETERMİNİSTİKTİR (ağ yok, gerçek `state/bars` yok) — beklenen alfa elle hesaplanabilsin diye.
"""
from __future__ import annotations

import inspect
import json
import os
import pathlib
import re

import pandas as pd
import pytest

from meridian import analytics, config, ledgerstamp, loop, run, store


# =================================================================================================
# YARDIMCILAR
# =================================================================================================
def _islem(i: int, ts_open: str, ts_close: str, pnl_pct: float, *, setup="breakout_vcp",
           regime="trend_up", bars_held=5, score=80, r=1.0, pnl=500.0, **ek) -> dict:
    return {"id": f"T{i:05d}", "ts_open": ts_open, "ts_close": ts_close, "ticker": "AAA",
            "side": "long", "entry": 100.0, "exit": 100.0 * (1 + pnl_pct), "qty": 10,
            "r_multiple": r, "pnl_pct": pnl_pct, "pnl_dollars": pnl, "costs": 5.0,
            "exit_reason": "target" if pnl_pct > 0 else "stop", "strategy_version": 4,
            "regime": regime, "setup": setup, "score": score, "bars_held": bars_held,
            "plan_id": f"P-{ts_open}-AAA", "skill_chain": ["vcp-screener"], **ek}


def _tohum_yazimi(trades: list, egri_son: str) -> None:
    """`run.replay_seed`in DİSKTEKİ İZİNİ birebir taklit et: defterin tamamı yazılır, HEMEN ardından
    equity_curve.json. `seed_boundary` sınırı tam olarak bu çiftten ölçer."""
    store.write_jsonl("trades.jsonl", trades)
    store.write_json("equity_curve.json",
                     {"version": 4, "points": [["2023-01-12", 100000.0], [egri_son, 94457.91]]})


def _spy_yaz(dates, closes) -> None:
    """Sandbox'a SENTETİK SPY defteri. Gerçek `state/bars` ASLA okunmaz — `_cache_path` sandbox'a
    bakar (izolasyon aşağıda ayrıca çivileniyor)."""
    from meridian.adapters import data as da
    df = pd.DataFrame({"date": pd.to_datetime(list(dates)),
                       "open": list(closes), "high": [c * 1.01 for c in closes],
                       "low": [c * 0.99 for c in closes], "close": list(closes),
                       "volume": [1e6] * len(closes)})
    df.to_csv(da._cache_path(da.INDEX_SYMBOL), index=False)


@pytest.fixture(autouse=True)
def _ag_yok(monkeypatch):
    """AĞA ÇIKIŞ KAPALI — BU DOSYANIN TÜM İDDİASI BUNA DAYANIYOR.

    Bunu yazdıran GERÇEK bir kaçaktı: `load_bars`ın tazelik koşulu (`cache.max >= end − 3g`)
    sağlanmadığında (ör. defterin `ts_close`u sentetik SPY'ın son barından ileri) fonksiyon
    sessizce `fetch()`e düşüyor ve OPERATÖRÜN gerçek SPY geçmişini çekiyordu — testler geçse bile
    ölçtükleri şey sentetik senaryo DEĞİL, o günkü piyasaydı (ilk koşuda tam olarak bu oldu:
    beklenen None yerine 0.03405 geldi).

    `fetch` boş çerçeve döndürünce `load_bars` önbelleğe geri düşer; yani ağ yokken üretimin
    yaptığının AYNISI olur — davranış taklit edilmiyor, YOLU kapatılıyor."""
    from meridian.adapters import data as da
    monkeypatch.setattr(da, "fetch", lambda *a, **k: pd.DataFrame())


# =================================================================================================
# A) İLERİ YOL — YENİ SATIR DAMGALI DOĞAR
# =================================================================================================
def test_A_canli_yol_her_satira_live_paper_basar(sandbox_state):
    """`loop._persist_trade` defterin İLERİ yoludur; buradan geçen satır canlı kâğıt döngünün
    GERÇEKTEN kapattığı işlemdir. Damga diske düşmeden basılır — sonradan damgalamak damgasız bir
    aralık doğururdu ve BT-1 tam olarak o aralıktı."""
    loop._persist_trade(_islem(1, "2026-07-21", "2026-07-24", 0.01))
    rows = store.read_jsonl("trades.jsonl")
    assert len(rows) == 1
    assert rows[0][ledgerstamp.FIELD] == ledgerstamp.LIVE_PAPER


def test_A_damga_tekilligi_BOZMAZ(sandbox_state):
    """ÇİVİ: damga, yinelenen-satır bastırmasının kimliğine karışmamalı. Karışsaydı bir çökme günü
    aynı işlemi ikinci kez deftere yazardı (denetim #11'in geri gelmesi)."""
    t = _islem(1, "2026-07-21", "2026-07-24", 0.01)
    loop._persist_trade(dict(t))
    loop._persist_trade(dict(t))
    assert len(store.read_jsonl("trades.jsonl")) == 1


def test_A_var_olan_damga_EZILMEZ(sandbox_state):
    """Bir satırın kökeni BİR KEZ ölçülür. İkinci bir yazar onu 'düzeltirse' migrasyonun kanıtı
    sessizce kaybolur — `stamp` var olan geçerli damgaya dokunmaz."""
    r = ledgerstamp.stamp({"a": 1, ledgerstamp.FIELD: ledgerstamp.REPLAY_SEED},
                          ledgerstamp.LIVE_PAPER)
    assert r[ledgerstamp.FIELD] == ledgerstamp.REPLAY_SEED


def test_A_gecersiz_damga_SESSIZCE_GECMEZ():
    """Yazım hatası bir damgayı sessizce 'belirsiz'e çevirseydi, defterin yarısı hiç fark
    edilmeden ölçüm dışına düşerdi. Geçersiz damga İSTİSNA fırlatır."""
    with pytest.raises(ValueError):
        ledgerstamp.stamp({}, "canli")
    with pytest.raises(TypeError):
        ledgerstamp.stamp_rows([["not", "a", "dict"]], ledgerstamp.LIVE_PAPER)


def test_A_CIVI_tohum_yazicisi_damgayi_basar_ve_egri_HEMEN_ardindan_gelir():
    """İKİ ÇİVİ BİR ARADA, çünkü ikisi TEK mekanizmanın iki yarısı:

      1. `run.replay_seed` defteri yazarken `ledgerstamp.stamp_rows(..., REPLAY_SEED)`den geçer;
      2. `equity_curve.json` yazımı HEMEN ardından gelir.

    (2) kozmetik değil ÖLÇÜM ALTYAPISIDIR: `seed_boundary` geriye dönük sınırı iki dosyanın mtime
    çiftinden okur. Araya başka bir yazım girerse imza bozulur ve migrasyon sessizce 'belirsiz'e
    düşer — yani BT-1 kısmen geri gelir."""
    src = pathlib.Path(inspect.getfile(run)).read_text()
    m = re.search(r'store\.write_jsonl\("trades\.jsonl",\s*(.+?)\)\n\s*store\.write_json\('
                  r'"equity_curve\.json"', src, re.S)
    assert m, "tohum yazımı ile equity_curve yazımı ARDIŞIK değil — sınır imzası bozuldu"
    assert "ledgerstamp.stamp_rows" in m.group(1) and "REPLAY_SEED" in m.group(1), m.group(1)


def test_A_stamp_rows_tumune_basar():
    rows = ledgerstamp.stamp_rows([{"id": "T1"}, {"id": "T2"}], ledgerstamp.REPLAY_SEED)
    assert [r[ledgerstamp.FIELD] for r in rows] == [ledgerstamp.REPLAY_SEED] * 2


# =================================================================================================
# B) GERİYE MİGRASYON — SINIR ÖLÇÜLÜR, UYDURULMAZ
# =================================================================================================
def test_B_sinir_egrinin_son_noktasindan_VE_mtime_ciftinden_olculur(sandbox_state):
    _tohum_yazimi([_islem(i, "2023-01-31", "2023-02-01", -0.01) for i in range(3)], "2026-07-20")
    b = ledgerstamp.seed_boundary()
    assert b["replay_end"] == "2026-07-20"
    assert b["toplu_yazim"] is True and b["guven"] == "yuksek"
    assert b["mtime_delta_s"] <= ledgerstamp.BULK_WRITE_TOLERANCE_S


def test_B_toplu_yazim_defterin_TAMAMINI_tohum_sayar(sandbox_state):
    """CANLI DEFTERİN DURUMU (2026-07-30 ölçümü): 95 satırın 95'i tohum. Toplu yazım imzası varsa
    diskteki her satır o yazımın ürünüdür — append mtime'ı ileri taşırdı."""
    _tohum_yazimi([_islem(i, "2023-01-31", f"2023-02-0{i+1}", -0.01) for i in range(3)],
                  "2026-07-20")
    rapor = ledgerstamp.migrate(apply=False)
    assert rapor["dagilim"] == {ledgerstamp.REPLAY_SEED: 3}
    assert rapor["sinif_ozeti"] == {"sinir_icinde": 3}


def test_B_kuru_kosu_HICBIR_BAYT_yazmaz(sandbox_state):
    """Veri yazan bir aracın varsayılanı yazmak olamaz (`barrepair` kuralı). Kanıt içerik DEĞİL
    mtime: içerik aynı kalsa bile yeniden yazım mtime'ı taşır ve sınır imzasını BOZARDI."""
    _tohum_yazimi([_islem(0, "2023-01-31", "2023-02-01", -0.01)], "2026-07-20")
    p = config.STATE / "trades.jsonl"
    once_mtime, once_icerik = p.stat().st_mtime_ns, p.read_text()
    rapor = ledgerstamp.migrate(apply=False)
    assert rapor["applied"] is False and rapor["yazildi"] is False and rapor["degisecek"] == 1
    assert p.stat().st_mtime_ns == once_mtime and p.read_text() == once_icerik


def test_B_uygula_yazar_ve_IDEMPOTENTTIR(sandbox_state):
    _tohum_yazimi([_islem(i, "2023-01-31", "2023-02-01", -0.01) for i in range(4)], "2026-07-20")
    r1 = ledgerstamp.migrate(apply=True)
    assert r1["yazildi"] is True and r1["degisecek"] == 4
    assert r1["sonraki_sayaclar"]["replay_seed_n"] == 4
    assert all(t[ledgerstamp.FIELD] == ledgerstamp.REPLAY_SEED
               for t in store.read_jsonl("trades.jsonl"))
    # İKİNCİ KOŞU HİÇBİR ŞEY YAPMAZ: aksi hâlde her migrasyon damgayı yeniden hesaplar ve bir gün
    # sınır kanıtı değiştiğinde geçmiş satırların kökeni sessizce değişirdi.
    p = config.STATE / "trades.jsonl"
    mtime = p.stat().st_mtime_ns
    r2 = ledgerstamp.migrate(apply=True)
    assert r2["degisecek"] == 0 and r2["yazildi"] is False
    assert p.stat().st_mtime_ns == mtime
    assert r2["sinif_ozeti"] == {"zaten_damgali": 4}


def test_B_migrasyon_islem_ALANLARINI_bozmaz(sandbox_state):
    """Damga EKLENİR; hiçbir mevcut alan kaybolmaz ya da değişmez."""
    once = [_islem(i, "2023-01-31", "2023-02-01", -0.01) for i in range(3)]
    _tohum_yazimi([dict(t) for t in once], "2026-07-20")
    ledgerstamp.migrate(apply=True)
    sonra = store.read_jsonl("trades.jsonl")
    for a, b in zip(once, sonra):
        assert {k: v for k, v in b.items() if k != ledgerstamp.FIELD} == a


def test_B_tohum_SONRASI_eklenen_satir_live_paper(sandbox_state):
    """Tohum yazımından SONRA `append` olmuşsa (mtime çifti ayrışır) sınırın ötesindeki satır canlı
    yoldan gelmiştir. Bu, canlı worker bir seans daha koştuğunda oluşacak normal hâldir."""
    _tohum_yazimi([_islem(i, "2023-01-31", "2023-02-01", -0.01) for i in range(2)], "2026-07-20")
    # equity_curve.json'ı GERİYE al: append'in mtime'ı ileri taşımasını taklit eder (testin
    # saniyeler beklemesi gerekmesin diye — ölçülen büyüklük FARKtır, mutlak zaman değil).
    eq = config.STATE / "equity_curve.json"
    eski = eq.stat().st_mtime - 10 * ledgerstamp.BULK_WRITE_TOLERANCE_S
    os.utime(eq, (eski, eski))
    store.append_jsonl("trades.jsonl", _islem(9, "2026-07-21", "2026-07-24", 0.02))
    b = ledgerstamp.seed_boundary()
    assert b["toplu_yazim"] is False and b["guven"] == "orta"
    rapor = ledgerstamp.migrate(apply=False)
    assert rapor["dagilim"] == {ledgerstamp.REPLAY_SEED: 2, ledgerstamp.LIVE_PAPER: 1}


def test_B_CELISKI_uydurulmaz_belirsiz_kalir(sandbox_state):
    """Toplu yazım imzası "defter o yazımdan beri değişmedi" derken sınırın ÖTESİNDE bir satır
    varsa iki kanıt çelişir. Sınıflandırıcı kendi kanıtını yalanlayamaz: satır `belirsiz` kalır."""
    _tohum_yazimi([_islem(0, "2023-01-31", "2023-02-01", -0.01),
                   _islem(1, "2026-07-21", "2026-07-24", 0.02)], "2026-07-20")
    rapor = ledgerstamp.migrate(apply=False)
    assert rapor["dagilim"] == {ledgerstamp.REPLAY_SEED: 1, ledgerstamp.BELIRSIZ: 1}
    assert rapor["sinif_ozeti"]["celiski_toplu_yazim"] == 1


def test_B_sinir_olculemezse_TUMU_belirsiz(sandbox_state):
    """UYDURMA YASAĞI: `equity_curve.json` yoksa tohum penceresinin sınırı bilinmez. Varsayılan bir
    tarih seçmek (ör. "bugün") defterin tamamını tek bir tahmine göre etiketlerdi."""
    store.write_jsonl("trades.jsonl", [_islem(0, "2023-01-31", "2023-02-01", -0.01)])
    b = ledgerstamp.seed_boundary()
    assert b["replay_end"] is None and b["guven"] == "yok"
    rapor = ledgerstamp.migrate(apply=False)
    assert rapor["dagilim"] == {ledgerstamp.BELIRSIZ: 1}
    assert rapor["sinif_ozeti"] == {"sinir_olculemedi": 1}


def test_B_bicimsiz_ts_close_belirsiz(sandbox_state):
    _tohum_yazimi([_islem(0, "2023-01-31", "2023-02-01", -0.01),
                   _islem(1, "2023-01-31", "yok", -0.01)], "2026-07-20")
    rapor = ledgerstamp.migrate(apply=False)
    assert rapor["dagilim"][ledgerstamp.BELIRSIZ] == 1
    assert rapor["sinif_ozeti"]["ts_close_ayristirilamadi"] == 1


def test_B_CLI_canli_surec_gorunce_YAZMAYI_REDDEDER(sandbox_state, monkeypatch, capsys):
    """`store` kilidi SÜREÇ-İÇİDİR (bu depoda belgeli): aynı defteri iki süreç yeniden yazamaz.
    Ret KOŞULSUZ değil — `--zorla` operatörün açık niyetidir."""
    _tohum_yazimi([_islem(0, "2023-01-31", "2023-02-01", -0.01)], "2026-07-20")
    p = config.STATE / "trades.jsonl"
    mtime = p.stat().st_mtime_ns
    monkeypatch.setattr(ledgerstamp, "_worker_running", lambda: True)
    assert ledgerstamp.main(["--uygula"]) == 2
    assert p.stat().st_mtime_ns == mtime, "ret sonrası deftere DOKUNULDU"
    assert "REDDEDİLDİ" in capsys.readouterr().err
    # --zorla ile yazar
    assert ledgerstamp.main(["--uygula", "--zorla"]) == 0
    assert store.read_jsonl("trades.jsonl")[0][ledgerstamp.FIELD] == ledgerstamp.REPLAY_SEED


def test_B_CLI_kuru_kosu_canli_surecte_bile_calisir(sandbox_state, monkeypatch):
    """Kuru koşu OKUMADIR; canlı süreç yüzünden reddedilmesi operatörü teşhisten mahrum bırakırdı."""
    _tohum_yazimi([_islem(0, "2023-01-31", "2023-02-01", -0.01)], "2026-07-20")
    monkeypatch.setattr(ledgerstamp, "_worker_running", lambda: True)
    assert ledgerstamp.main([]) == 0
    assert ledgerstamp.FIELD not in store.read_jsonl("trades.jsonl")[0]


def test_B_CLI_json_makine_okunur(sandbox_state, monkeypatch, capsys):
    _tohum_yazimi([_islem(0, "2023-01-31", "2023-02-01", -0.01)], "2026-07-20")
    monkeypatch.setattr(ledgerstamp, "_worker_running", lambda: False)
    ledgerstamp.main(["--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["sinir"]["replay_end"] == "2026-07-20" and d["degisecek"] == 1


def test_B_worker_olcumu_barrepair_ILE_AYNI_FONKSIYON():
    """İki kopya = iki farklı "canlı" tanımı; biri diğerini sessizce yalanlar (bu depoda yaşanmış
    sınıf). Ölçüm kopyalanmaz, ÇAĞRILIR."""
    src = inspect.getsource(ledgerstamp._worker_running)
    assert "from .barrepair import _worker_running" in src


# =================================================================================================
# C) AYRIŞTIRILMIŞ SAYAÇLAR — KARNE, KALİBRASYON, PANO
# =================================================================================================
def test_C_sayaclar_uc_kovayi_da_AYIRIR(sandbox_state):
    store.write_jsonl("trades.jsonl", [
        dict(_islem(0, "2026-07-21", "2026-07-24", 0.01), kaynak=ledgerstamp.LIVE_PAPER),
        dict(_islem(1, "2023-01-31", "2023-02-01", -0.01), kaynak=ledgerstamp.REPLAY_SEED),
        dict(_islem(2, "2023-01-31", "2023-02-01", -0.01), kaynak=ledgerstamp.BELIRSIZ),
        _islem(3, "2023-01-31", "2023-02-01", -0.01),                       # DAMGASIZ
    ])
    c = ledgerstamp.counts()
    assert c["live_paper_n"] == 1 and c["replay_seed_n"] == 1
    assert c["belirsiz_n"] == 2, "damgasız satır 'kökeni bilinmeyen' kovasına girmeli"
    assert c["damgasiz_n"] == 1 and c["toplam"] == 4
    assert c["training_n"] == c["replay_seed_n"]


def test_C_tanimsiz_damga_belirsiz_sayilir(sandbox_state):
    """Gelecekte biri elle "kaynak: gölge" yazarsa sayaç onu canlı sanmamalı."""
    store.write_jsonl("trades.jsonl", [dict(_islem(0, "2023-01-31", "2023-02-01", 0.0),
                                            kaynak="golge")])
    c = ledgerstamp.counts()
    assert c["belirsiz_n"] == 1 and c["live_paper_n"] == 0
    assert c["damgasiz_n"] == 0, "damgası VAR ama tanınmıyor — 'hiç damgalanmamış' ile aynı şey değil"


def test_C_split_paydalari_ayirir(sandbox_state):
    store.write_jsonl("trades.jsonl", [
        dict(_islem(0, "2026-07-21", "2026-07-24", 0.01), kaynak=ledgerstamp.LIVE_PAPER),
        dict(_islem(1, "2023-01-31", "2023-02-01", -0.01), kaynak=ledgerstamp.REPLAY_SEED)])
    s = ledgerstamp.split()
    assert len(s[ledgerstamp.LIVE_PAPER]) == 1 and len(s[ledgerstamp.REPLAY_SEED]) == 1


def test_C_karne_gercek_canliyi_TOHUMDAN_ayirir(sandbox_state):
    """BT-1'in özü: karne 95 satırı canlı sanıyordu. `gercek_canli_n` yalnız KANITLI canlı satırı
    sayar; tohum `training_n`de durur (gizlenmez, olgunluk sayılmaz)."""
    store.write_jsonl("trades.jsonl",
                      [dict(_islem(i, "2023-01-31", "2023-02-01", -0.01),
                            kaynak=ledgerstamp.REPLAY_SEED) for i in range(40)]
                      + [dict(_islem(90, "2026-07-21", "2026-07-24", 0.01),
                              kaynak=ledgerstamp.LIVE_PAPER)])
    sc = analytics.learning_scorecard()
    d = sc["defter"]
    assert sc["trades_total"] == 41, "ham satır sayısı geriye dönük uyum için AYNEN kalmalı"
    assert d["gercek_canli_n"] == 1 and d["training_n"] == 40
    assert d["orneklem_n"] == 1                       # tohum paydaya girmez
    assert d["sinir"]["replay_end"] is None or isinstance(d["sinir"]["replay_end"], str)


def test_C_min_sample_paydasi_TOHUMU_saymaz(sandbox_state, monkeypatch):
    """Eskiden payda `strategy_version == cur_v` olan HER satırdı; tohum defterin tamamını cur_v ile
    damgaladığı için sayaç bir gecede dolu görünüyordu — ölçülmemiş bir olgunluk iddiası."""
    monkeypatch.setattr(analytics.memory, "all_hypotheses",
                        lambda: [{"status": "live", "version_to": 4}])
    monkeypatch.setattr(analytics, "calibration",
                        lambda *a, **k: {"n": 0, "hit_rate": None, "brier": None})
    store.write_json("scoreboard.json", {"current_version": 4, "versions": {"4": {}}})
    store.write_jsonl("trades.jsonl",
                      [dict(_islem(i, "2023-01-31", "2023-02-01", -0.01),
                            kaynak=ledgerstamp.REPLAY_SEED) for i in range(50)]
                      + [dict(_islem(90 + i, "2026-07-21", "2026-07-24", 0.01),
                              kaynak=ledgerstamp.LIVE_PAPER) for i in range(2)])
    sc = analytics.learning_scorecard(goal={"min_sample": 30})
    assert sc["loop_state"] == "shipped_awaiting_min_sample"
    assert "2/30" in sc["verdict"], sc["verdict"]
    assert "50 tohum/training" in sc["verdict"], "tohum GİZLENMEMELİ, yalnız olgunluk sayılmamalı"


def test_C_damgasiz_defter_ESKI_gibi_sayilir(sandbox_state, monkeypatch):
    """GERİYE-UYUM + DÜRÜSTLÜK SINIRI: damgasız satır tohum SAYILMAZ (kanıtımız yok). Migrasyondan
    önceki dünyada karne eskisi gibi davranır; yalancı bir 0 basmaz."""
    monkeypatch.setattr(analytics.memory, "all_hypotheses",
                        lambda: [{"status": "live", "version_to": 4}])
    monkeypatch.setattr(analytics, "calibration",
                        lambda *a, **k: {"n": 0, "hit_rate": None, "brier": None})
    store.write_json("scoreboard.json", {"current_version": 4, "versions": {"4": {}}})
    store.write_jsonl("trades.jsonl", [_islem(i, "2023-01-31", "2023-02-01", -0.01)
                                       for i in range(5)])
    sc = analytics.learning_scorecard(goal={"min_sample": 30})
    assert "5/30" in sc["verdict"] and "tohum/training" not in sc["verdict"]
    assert sc["defter"]["gercek_canli_n"] == 0 and sc["defter"]["orneklem_n"] == 5


def test_C_karne_ESKI_anahtarlari_KORUR(sandbox_state):
    """Pano eski alanlara bağlı (web/* bu turda başka bir kolda) — yeni alan EKLENİR, eski kalır."""
    store.write_jsonl("trades.jsonl", [_islem(0, "2023-01-31", "2023-02-01", 0.0)])
    sc = analytics.learning_scorecard()
    for eski in ("status_counts", "shipped", "outcomes_measured", "loop_state", "calibration",
                 "min_sample", "verdict", "trades_total", "besleme"):
        assert eski in sc, eski
    assert "defter" in sc


def test_C_skor_kalibrasyonu_GERCEK_dilimi_kaynaga_gore_acar(sandbox_state, monkeypatch):
    """cf dilimini ayırmakla çözülen sorunun aynısı, bu kez GERÇEK dilimin İÇİNDE: raporlanan
    "skorun tahmin gücü" fiilen SİMÜLE bir defterin IC'siydi."""
    from meridian import counterfactual
    monkeypatch.setattr(counterfactual, "resolved_rows", lambda **k: [])
    rows = []
    for i in range(40):
        rows.append(dict(_islem(i, "2023-01-31", "2023-02-01", 0.0, score=50 + i,
                                r=(i - 20) / 10.0), kaynak=ledgerstamp.REPLAY_SEED))
    for i in range(5):
        rows.append(dict(_islem(100 + i, "2026-07-21", "2026-07-24", 0.0, score=60 + i,
                                r=float(i)), kaynak=ledgerstamp.LIVE_PAPER))
    store.write_jsonl("trades.jsonl", rows)
    cal = analytics.score_calibration()
    assert cal is not None
    gk = cal["gercek_kaynak"]
    assert gk[ledgerstamp.REPLAY_SEED]["n"] == 40 and gk[ledgerstamp.LIVE_PAPER]["n"] == 5
    assert gk[ledgerstamp.REPLAY_SEED]["ic"] is not None, "40 satır IC eşiğini geçmeli"
    # 5 satır <30 → ÖLÇÜLMEDİ. Sahte bir IC basmak, kalibrasyonun en tehlikeli yalanı olurdu.
    assert gk[ledgerstamp.LIVE_PAPER]["ic"] is None
    # AYRI EKSEN, `katmanlar`ın DÖRDÜNCÜ KOVASI DEĞİL: `katmanlar` gerçek/cf/havuz üçlüsüdür ve
    # tüketiciler onu tek şekilli üç kova olarak dolaşır (v108 bu üçlüyü adıyla kilitliyor).
    # Kaynak kırılımı "gerçek" kovasının İÇ eksenidir; oraya girseydi bir katman sanılırdı.
    assert set(cal["katmanlar"]) == {"gercek", "cf", "havuz"}


# =================================================================================================
# D) ALFA/BETA KOLONU — SENTETİK SPY İLE DETERMİNİSTİK
# =================================================================================================
def test_D_sandbox_izolasyonu_gercek_barlara_DOKUNMAZ(sandbox_state):
    """Bu bloğun tüm iddiası "SPY sentetik" olmasına dayanıyor. Yol sandbox'a bakmıyorsa testler
    operatörün gerçek defterini ölçer ve geçtiklerinde hiçbir şey KANITLAMAZ."""
    from meridian.adapters import data as da
    assert str(da._cache_path(da.INDEX_SYMBOL)).startswith(str(sandbox_state))


def test_D_alfa_ELLE_HESAPLANABILIR_deger_uretir(sandbox_state):
    """DETERMİNİSTİK ÇEKİRDEK: SPY 100→110 (+%10) ve 110→121 (+%10) pencerelerinde; işlemler
    +%12 ve +%8 üretti → ortalama işlem %10, ortalama SPY %10, ort_fark 0. Sayı elle
    doğrulanabilir olmasaydı test yalnız "patlamadı"yı kanıtlardı."""
    _spy_yaz(["2026-01-05", "2026-01-06", "2026-01-07"], [100.0, 110.0, 121.0])
    store.write_jsonl("trades.jsonl", [
        _islem(0, "2026-01-05", "2026-01-06", 0.12),      # SPY +%10, işlem +%12 → fark +%2
        _islem(1, "2026-01-06", "2026-01-07", 0.08),      # SPY +%10, işlem +%8  → fark −%2
    ])
    ab = analytics.trade_alpha_beta()
    assert ab["n_olculebilir"] == 2 and ab["n_olculemeyen"] == 0
    assert ab["ort_spy"] == pytest.approx(0.10, abs=1e-9)
    assert ab["ort_islem"] == pytest.approx(0.10, abs=1e-9)
    assert ab["ort_fark"] == pytest.approx(0.0, abs=1e-9)
    assert ab["benchmark"] == "SPY"


def test_D_kazananlarin_SPY_penceresi_AYRI_olculur(sandbox_state):
    """DENETİMİN ASIL BULGUSU: kazananlar SPY'ın da koştuğu pencerelerdeyse "kazandık" cümlesi
    seçim değil BETA anlatır. Canlı defterde kazananların SPY ortalaması +%1,89'du."""
    # 01-05→01-06 SPY +%10 (kazanan burada), 01-06→01-07 SPY −%10 (kaybeden burada)
    _spy_yaz(["2026-01-05", "2026-01-06", "2026-01-07"], [100.0, 110.0, 99.0])
    store.write_jsonl("trades.jsonl", [
        _islem(0, "2026-01-05", "2026-01-06", 0.05),      # KAZANAN, SPY +%10
        _islem(1, "2026-01-06", "2026-01-07", -0.05),     # KAYBEDEN, SPY −%10
    ])
    ab = analytics.trade_alpha_beta()
    assert ab["kazanan_n"] == 1 and ab["kaybeden_n"] == 1
    assert ab["kazananlarin_spy_ortalamasi"] == pytest.approx(0.10, abs=1e-9)
    assert ab["kaybedenlerin_spy_ortalamasi"] == pytest.approx(-0.10, abs=1e-9)


def test_D_kirilim_aile_rejim_tutus_dilimi(sandbox_state):
    _spy_yaz(["2026-01-05", "2026-01-06", "2026-01-07"], [100.0, 100.0, 100.0])   # SPY DÜMDÜZ
    store.write_jsonl("trades.jsonl", [
        _islem(0, "2026-01-05", "2026-01-06", 0.04, setup="breakout_vcp",
               regime="trend_up", bars_held=1),
        _islem(1, "2026-01-05", "2026-01-06", 0.02, setup="breakout_vcp",
               regime="trend_up", bars_held=1),
        _islem(2, "2026-01-06", "2026-01-07", -0.06, setup="pullback",
               regime="chop", bars_held=10),
    ])
    ab = analytics.trade_alpha_beta()
    k = ab["kirilim"]
    # SPY sabit → fark = işlem getirisi (kırılım aritmetiği elle doğrulanabilir)
    assert k["aile"]["breakout_vcp"]["n"] == 2
    assert k["aile"]["breakout_vcp"]["ort_fark"] == pytest.approx(0.03, abs=1e-9)
    assert k["aile"]["pullback"]["ort_fark"] == pytest.approx(-0.06, abs=1e-9)
    assert k["rejim"]["chop"]["n"] == 1 and k["rejim"]["trend_up"]["n"] == 2
    assert k["tutus_dilimi"]["1g"]["n"] == 2 and k["tutus_dilimi"]["8-15g"]["n"] == 1
    # ÇAPRAZ HÜCRELER: aile × rejim × dilim
    hucreler = {(h["aile"], h["rejim"], h["tutus_dilimi"]): h for h in k["hucreler"]}
    assert ("breakout_vcp", "trend_up", "1g") in hucreler
    assert ("pullback", "chop", "8-15g") in hucreler
    assert hucreler[("breakout_vcp", "trend_up", "1g")]["n"] == 2


def test_D_seyrek_hucre_DEGERI_gizlemez_ETIKETLER(sandbox_state):
    """"n yetersiz" ile "ölçüm yok" aynı cümle değildir: değer görünür, `yeterli: False` yanında."""
    _spy_yaz(["2026-01-05", "2026-01-06"], [100.0, 100.0])
    store.write_jsonl("trades.jsonl", [_islem(0, "2026-01-05", "2026-01-06", 0.04)])
    h = analytics.trade_alpha_beta()["kirilim"]["aile"]["breakout_vcp"]
    assert h["n"] == 1 and h["yeterli"] is False and h["ort_fark"] == pytest.approx(0.04)
    assert analytics.ALFA_HUCRE_MIN_N == 5


def test_D_ayni_seans_kapanisi_0g_dilimidir_OLCULEMEDI_degil(sandbox_state):
    """`bars_held=0` ÖLÇÜLMÜŞ bir tutuştur (canlı defterde var: T00070/TDG 2025-05-06).
    "olculemedi" kovasına düşürmek, ölçülmüş bir değeri ölçülmemiş göstermek olurdu."""
    _spy_yaz(["2026-01-05"], [100.0])
    store.write_jsonl("trades.jsonl", [_islem(0, "2026-01-05", "2026-01-05", 0.0, bars_held=0),
                                       _islem(1, "2026-01-05", "2026-01-05", 0.0, bars_held=None)])
    k = analytics.trade_alpha_beta()["kirilim"]["tutus_dilimi"]
    assert k["0g"]["n"] == 1 and k["olculemedi"]["n"] == 1


def test_D_kaynak_kirilimi_TOHUMU_canliyla_KARISTIRMAZ(sandbox_state):
    """BT-1 ↔ AT-1 bağlantısı: tohum satırlarının alfası "kuralların karakteri"dir, canlı
    performans DEĞİL. Tek ortalamada toplamak denetimin şikâyet ettiği karışımın ta kendisi."""
    _spy_yaz(["2026-01-05", "2026-01-06"], [100.0, 100.0])
    store.write_jsonl("trades.jsonl", [
        dict(_islem(0, "2026-01-05", "2026-01-06", 0.04), kaynak=ledgerstamp.REPLAY_SEED),
        dict(_islem(1, "2026-01-05", "2026-01-06", -0.02), kaynak=ledgerstamp.LIVE_PAPER)])
    kk = analytics.trade_alpha_beta()["kaynak_kirilim"]
    assert kk[ledgerstamp.REPLAY_SEED]["ort_fark"] == pytest.approx(0.04, abs=1e-9)
    assert kk[ledgerstamp.LIVE_PAPER]["ort_fark"] == pytest.approx(-0.02, abs=1e-9)


# ---- NONE YOLLARI: ÖLÇÜLEMEYEN ÖLÇÜLMÜŞ GİBİ GÖSTERİLMEZ -------------------------------------
def test_D_NONE_spy_hic_yoksa(sandbox_state):
    store.write_jsonl("trades.jsonl", [_islem(0, "2026-01-05", "2026-01-06", 0.04)])
    ab = analytics.trade_alpha_beta()
    assert ab["ort_fark"] is None and ab["neden_bos"], "sebep görünmezse kimse aramaz"
    assert ab["kirilim"]["aile"] == {} and ab["kaynak_kirilim"] == {}


def test_D_NONE_defter_bosken(sandbox_state):
    store.write_jsonl("trades.jsonl", [])
    ab = analytics.trade_alpha_beta()
    assert ab["n"] == 0 and ab["ort_fark"] is None and ab["neden_bos"] == "defter boş"


def test_D_penceresi_OLCULEMEYEN_islem_ortalamaya_GIRMEZ(sandbox_state):
    """SPY barı olmayan tarihe düşen işlem `n_olculemeyen`e yazılır ve HİÇBİR ortalamaya girmez —
    eksik barı komşusuyla doldurmak (asof/ffill) ölçülmemiş bir kesinlik yazardı."""
    _spy_yaz(["2026-01-05", "2026-01-06", "2026-01-09"], [100.0, 112.0, 120.0])
    store.write_jsonl("trades.jsonl", [
        _islem(0, "2026-01-05", "2026-01-06", 0.12),      # SPY +%12
        _islem(1, "2026-01-07", "2026-01-09", 5.00),      # 01-07 SPY'da YOK — sayılmaz
    ])
    ab = analytics.trade_alpha_beta()
    assert ab["n"] == 2 and ab["n_olculebilir"] == 1 and ab["n_olculemeyen"] == 1
    assert ab["ort_islem"] == pytest.approx(0.12, abs=1e-9)
    assert ab["ort_spy"] == pytest.approx(0.12, abs=1e-9)


def test_D_hicbir_pencere_olculemezse_NONE(sandbox_state):
    """SPY defteri DOLU ama hiçbir işlem penceresinin İKİ ucu da barlarda yok. "Bar yok" ile
    "bar var ama bu tarihler yok" iki ayrı arızadır ve ikisi ayrı `neden_bos` metni taşır."""
    _spy_yaz(["2026-01-05", "2026-01-07", "2026-01-09"], [100.0, 110.0, 120.0])
    store.write_jsonl("trades.jsonl", [
        _islem(0, "2026-01-05", "2026-01-06", 0.12),      # kapanış barı yok
        _islem(1, "2026-01-08", "2026-01-09", 0.10),      # açılış barı yok
    ])
    ab = analytics.trade_alpha_beta()
    assert ab["ort_fark"] is None and ab["n_olculemeyen"] == 2
    assert ab["neden_bos"] == "hiçbir işlemin SPY penceresi ölçülemedi"


def test_D_pnl_pct_yoksa_olculemez(sandbox_state):
    _spy_yaz(["2026-01-05", "2026-01-06"], [100.0, 110.0])
    t = _islem(0, "2026-01-05", "2026-01-06", 0.12)
    t.pop("pnl_pct")
    store.write_jsonl("trades.jsonl", [t])
    assert analytics.trade_alpha_beta()["n_olculemeyen"] == 1


# =================================================================================================
# E) HÜKME BAĞLANMA — KOLON, BEŞİNCİ ÖLÇÜT DEĞİL
# =================================================================================================
def test_E_beta_kolonu_DORT_OLCUTU_degistirmez(sandbox_state):
    """SÖZLEŞME: dört ölçüt bu depoda yazılıdır (`passed/4` cümlesi, health.sonuc_hukmu kapısı,
    /api/diagnostics tüketicisi, mevcut testler). Beşinci ölçüt eklemek hiçbir eşiği
    değiştirmeden hükmü kaydırırdı — habersiz hüküm kayması YASAK."""
    _spy_yaz(["2026-01-05", "2026-01-06"], [100.0, 110.0])
    store.write_jsonl("trades.jsonl", [_islem(i, "2026-01-05", "2026-01-06", -0.05, pnl=-300.0,
                                              r=-1.0) for i in range(40)])
    rv = analytics.result_verdict()
    assert set(rv["criteria"]) == {"dolar_beklenti", "profit_factor", "maks_dusus", "net_pnl"}
    assert rv["passed"] + rv["failed"] + rv["unmeasured"] + rv["zayif"] == len(rv["criteria"]) == 4
    assert f"{rv['passed']}/4 sağlandı" in rv["verdict"]
    b = rv["beta_duzeltilmis"]
    assert b["hukme_girmez"] is True and "ADVISORY" in b["kapsam"]
    assert b["durum"] == "negatif" and b["ort_fark"] == pytest.approx(-0.15, abs=1e-9)


def test_E_beta_kolonu_olculemedigi_zaman_DURUST_bos(sandbox_state):
    store.write_jsonl("trades.jsonl", [_islem(i, "2026-01-05", "2026-01-06", -0.05, pnl=-300.0)
                                       for i in range(40)])
    b = analytics.result_verdict()["beta_duzeltilmis"]
    assert b["durum"] == "olculemedi" and b["ort_fark"] is None and b["neden_bos"]


@pytest.fixture
def client(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient

    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    return TestClient(api.app)


def test_E_YASA6_api_today_defter_sayacini_TASIR(client, sandbox_state):
    """Gerçek-canlı sayacın DIŞ tüketicisi: /api/today. Alan hazır; pano turu bağlayacak."""
    store.write_jsonl("trades.jsonl", [
        dict(_islem(0, "2026-07-21", "2026-07-24", 0.01), kaynak=ledgerstamp.LIVE_PAPER),
        dict(_islem(1, "2023-01-31", "2023-02-01", -0.01), kaynak=ledgerstamp.REPLAY_SEED),
        _islem(2, "2023-01-31", "2023-02-01", -0.01)])
    d = client.get("/api/today")
    assert d.status_code == 200
    defter = d.json()["defter"]
    assert {"live_paper_n", "replay_seed_n", "belirsiz_n"} <= set(defter)
    assert defter["live_paper_n"] == 1 and defter["replay_seed_n"] == 1
    assert defter["belirsiz_n"] == 1


def test_E_YASA6_diagnostics_alfa_beta_ve_defter_kaynagini_TASIR(client, sandbox_state):
    _spy_yaz(["2026-01-05", "2026-01-06"], [100.0, 110.0])
    store.write_jsonl("trades.jsonl", [
        dict(_islem(i, "2026-01-05", "2026-01-06", -0.05, pnl=-300.0, r=-1.0),
             kaynak=ledgerstamp.REPLAY_SEED) for i in range(40)])
    ml = client.get("/api/diagnostics").json()["mlops"]
    ab = ml["alpha_beta"]
    assert ab is not None and ab["ort_fark"] == pytest.approx(-0.15, abs=1e-9)
    assert ab["kirilim"]["aile"]["breakout_vcp"]["n"] == 40
    # İKİ YÜZEY TEK GERÇEK: aynı yanıtta iki farklı alfa belirirse okur hangisine inanacağını
    # bilemez. (Telde JSON kimliği kaybolur; PAYLAŞIM'ın kendisi aşağıdaki kaynak çivisiyle
    # kanıtlanıyor — burada eşitlik, orada tek-hesap.)
    assert ml["alpha_beta"] == ml["result_verdict"]["beta_duzeltilmis"]
    ls = ml["ledger_source"]
    assert ls["replay_seed_n"] == 40 and ls["live_paper_n"] == 0


def test_E_CIVI_diagnostics_alfayi_IKINCI_KEZ_hesaplamaz():
    """`trade_alpha_beta` SPY barlarını DİSKTEN okur. /api/diagnostics onu ikinci kez çağırsaydı
    (a) her pano anketinde aynı iş iki kez yapılır, (b) tek yanıtta iki ayrı okuma anı doğardı —
    `edge_verdict`/`result_verdict`/`validation_trio` üçlüsünün paylaşım gerekçesiyle AYNI.
    Yüzey, hükmün İÇİNDE zaten hesaplanmış olan nesneyi servis eder."""
    from meridian import api
    src = pathlib.Path(inspect.getfile(api)).read_text()
    blok = src[src.index("def api_diagnostics"):src.index("def api_diagnostics") + 40000]
    assert '"alpha_beta": _sonuc_v.get("beta_duzeltilmis")' in blok
    assert "an.trade_alpha_beta()" not in blok, "alfa/beta ikinci kez hesaplanıyor"

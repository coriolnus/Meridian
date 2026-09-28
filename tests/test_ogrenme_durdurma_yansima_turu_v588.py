"""test_ogrenme_durdurma_yansima_turu_v588.py — kesilen yansıma turu SAYILMAZ + replay gün kontrol noktası (TSK-248).

KARAR (operatör ONAYLI 2026-09-28, `docs/TASARIM-OGRENME-DURDURMA-2026-09-28.md` §2): A — durdurma bir yansıma
turunun ortasında gelirse tur HİÇ SAYILMAZ: K/aşınma defterine (`validation.record_candidate`), hipotez defterine
(`memory.record`) hiçbir satır düşmez, ship olmaz, `last_reflect_at` İLERLEMEZ; süreç yeniden başlayınca aynı
kanıtla yeniden dener. Seçenek 1 — `backtest.replay` gün döngüsüne opsiyonel durdurma yüklemi: TEK bir
walk-forward da artık bölünebilir (TSK-246'nın beyanlı SINIRI kapanır); durdurmada `backtest.ReplayDurduruldu`
yukarı taşınır, sonuç ÖNBELLEĞE YAZILMAZ.

VAKA ZEMİNİ (TSK-246 raporu §8.1, kod okuması 2026-09-28): `reflect_once → submit` ve `search_and_submit →
coordinate_descent_search` zinciri durdurma yüklemini İLETMİYORDU; `_run` tur dönene dek bloklanıyordu ve
`TimeoutStopSec` dolunca SIGKILL iki gerçek risk bırakıyordu — (i) K/aşınma defterine düşmüş ama hipotez
defterinde karşılığı olmayan satır (asimetrik defter), (ii) karar yazılmış ama `last_reflect_at` eski.

ÇİVİ KÜMESİ:
  A) replay: bayraksız yol BİT-ÖZDEŞ (eski/yeni imza) · yüklem gün başına BİR kez · ortasında bayrak → istisna ·
     walk_forward yüklemi iletir, yoksa anahtarı HİÇ geçirmez · maliyet ÖLÇÜMÜ.
  B) önbellek: `_wf_cached` / `_probe_wf` durdurmada YAZMAZ.
  C) submit: dört kontrol noktası (giriş · incumbent öncesi · aday öncesi · `_gate_eval` öncesi) + walk-forward
     ortası → hiçbir defter satırı yok; bayrak kurulmamışken defterler BİREBİR (ikiz kum havuzu).
  D) arama: `search_and_submit` yüklemi İLETİR (bugün iletmiyordu — kırmızı başlar); kesilen aramada kazanan
     varken submit YOK, kazanan yokken oturum kaydı YOK; sonda ortasında istisna → sayım muhasebesi tutar.
  E) hermes: öneri turu kesilince aramaya DÜŞÜLMEZ; yüklem zincire iletilir; girişte bayrak → LLM çağrılmaz.
  F) hermes_runtime: kesilen canlı / arka plan / elle turu SAYILMAZ (`_record` yok, tabanlar sabit, istek dosyası
     KALIR); uçtan uca SIGTERM → iniş ÖLÇÜMÜ (gerçek replay, hedef ≤30 sn).
  G) import sözleşmesi: yüklem ENJEKTE edilir — `reflect`/`backtest` `hermes_runtime`i tanımaz.

CANLI STATE'E YAZILMAZ: her state testi `sandbox_state` içinde; gerçek işçi SÜRECİ başlatılmaz.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import datetime as dt
import json
import re
import shutil
import signal
import statistics
import threading
import time
import types
from pathlib import Path

import pytest

from meridian import (backtest, config, health, hermes, learn_run, memory, reflect, store, validation,
                      versioning, watchdog)
from meridian import hermes_runtime as hr
from meridian import strategy as strategy_mod
from meridian.strategy import EntrySignal
from tests import wf_fixtures as wf
from tests.conftest import make_bars

REPO = Path(__file__).resolve().parents[1]
KNOB, SMALL, FULL = "position_size_r", 0.1, 1.0
# Kesilen turda DEĞİŞMESİNE izin verilen dosyalar: olay defteri (beyan), yansıma kilidi, TAMAMLANMIŞ
# incumbent/sonda walk-forward'larının önbelleği (tam hesaplar — yarım ölçüm değil) ve ilerleme/durum aynaları. Geri kalan HER dosya
# (hipotez + kimlik HWM, doğrulama defteri, aşınma sayacı, strateji, karne, sürüm geçmişi) byte-byte aynı kalır.
DEFTER_DISI = {"events.jsonl", ".reflect.lock", "inc_cache.json", "probe_cache.json", "search_progress.json",
               "hermes_status.json"}


# =================================================================================================
# ORTAK SAHNE — gerçek replay için sentetik evren (v427 deseni: tarama deterministik saplama)
# =================================================================================================
N_BARS = 200
TICKERS = {"MEM": 2, "AAA": 3, "BBB": 4}


def _ohlc(df):
    df = df.copy()
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


def _mem_sinyali(bars_df, params, rs_rating_value, ticker="?"):
    """`strategy.scan_entry` saplaması (v427 ile aynı): yalnız MEM için deterministik sinyal — sahne işlem
    üretsin ki bit-özdeşlik kıyası BOŞ olmasın."""
    if ticker != "MEM":
        return None
    close = float(bars_df["close"].iloc[-1])
    entry = close * 1.001
    stop = entry * 0.95
    r = entry - stop
    return EntrySignal(ticker=ticker, setup="momentum_breakout", entry_trigger=entry, pivot=entry,
                       stop=stop, atr=r / 2.0, rs_rating=80, score=80, profit_target=entry + 3.0 * r,
                       size_r=0.5, r_per_share=r, notes="v588-sentetik-sinyal")


def _onbellek_sifirla() -> None:
    reflect._INC_CACHE.clear()
    reflect._PROBE_CACHE.clear()
    reflect._INC_DISK_LOADED = False
    reflect._PROBE_DISK_LOADED = False


@pytest.fixture
def sahne(sandbox_state, monkeypatch):
    monkeypatch.setattr(strategy_mod, "scan_entry", _mem_sinyali)
    idx = _ohlc(make_bars(N_BARS, seed=7, trend=0.0006))
    bars = {t: _ohlc(make_bars(N_BARS, seed=s, trend=0.0008)) for t, s in TICKERS.items()}
    dates = [str(x.date()) for x in idx["date"]]
    w = (dates[0], dates[100], dates[150], dates[-1], [dates[115], dates[130], dates[150]], 0)
    _onbellek_sifirla()
    yield {"bars": bars, "idx": idx, "params": config.default_strategy()["params"], "goal": config.goal(),
           "dates": dates, "w": w}
    _onbellek_sifirla()


def _replay(s, **kw):
    return backtest.replay(s["params"], s["bars"], s["idx"], s["goal"], s["dates"][0], s["dates"][-1],
                           strategy_version=1, **kw)


def _wf(s, **kw):
    w = s["w"]
    return backtest.walk_forward(s["params"], s["bars"], s["idx"], s["goal"], w[0], w[1], w[2], w[3],
                                 oos_folds=w[4], embargo_days=w[5], **kw)


def _parmak(nesne) -> str:
    if dataclasses.is_dataclass(nesne):
        nesne = dataclasses.asdict(nesne)
    return json.dumps(nesne, sort_keys=True, default=str)


def _sayac_sonra(k: int):
    """k okumadan SONRA kurulan bayrak (k+1. okuma True) + okuma sayacı."""
    n = {"c": 0}

    def _y() -> bool:
        n["c"] += 1
        return n["c"] > k
    return _y, n


def _olaylar(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


def _foto(kok: Path) -> dict:
    return {p.relative_to(kok).as_posix(): p.read_bytes() for p in kok.rglob("*") if p.is_file()}


def _degisen(once: dict, sonra: dict) -> set:
    return {k for k in set(once) | set(sonra) if once.get(k) != sonra.get(k)}


# =================================================================================================
# A) REPLAY — gün başı kontrol noktası
# =================================================================================================
def test_replay_bayraksiz_BIT_OZDES_eski_ve_yeni_imza(sahne):
    """POZİTİF KONTROL (brief §4): aynı girdiyle eski imza (kwarg yok) ve yeni imza (None / hiç kurulmayan
    yüklem) BİREBİR aynı sonucu üretir — işlemler, eğri, plan/aday kaydı, sayaçlar. Kıyas BOŞ değildir."""
    eski = _replay(sahne)
    assert len(eski.trades) >= 5, f"sahne az işlem üretti ({len(eski.trades)}) — kıyas zayıf"
    for kw in ({"durdurma": None}, {"durdurma": lambda: False}, {"durdurma": threading.Event().is_set}):
        assert _parmak(_replay(sahne, **kw)) == _parmak(eski), f"replay {kw} ile SAPTI"
    wf_eski = _wf(sahne)
    assert wf_eski["n_trades_total"] >= 5
    assert _parmak(_wf(sahne, durdurma=lambda: False)) == _parmak(wf_eski), "walk_forward kurulmamış yüklemle SAPTI"


def test_replay_yuklemi_GUN_BASINA_BIR_KEZ_sorar(sahne):
    """Maliyet modeli: takvim günü başına TAM bir yüklem çağrısı (sembol/faz başına DEĞİL)."""
    y, n = _sayac_sonra(10 ** 9)
    _replay(sahne, durdurma=y)
    assert n["c"] == N_BARS, f"yüklem {n['c']} kez soruldu — {N_BARS} günlük takvimde gün başına BİR beklenir"


def test_replay_ortasinda_bayrak_ReplayDurduruldu_firlatir(sahne):
    """K gün tamamlandıktan sonra kurulan bayrak (K+1). günün BAŞINDA görülür; istisna tamamlanan gün sayısını,
    takvim boyunu ve kesilen günü taşır. Tamamlanan günler DEĞİŞMEZ (kısmi sonuç döndürülmez — istisna)."""
    K = 37
    y, n = _sayac_sonra(K)
    with pytest.raises(backtest.ReplayDurduruldu) as z:
        _replay(sahne, durdurma=y)
    assert n["c"] == K + 1, n
    assert (z.value.tamamlanan_gun, z.value.toplam_gun, z.value.tarih) == (K, N_BARS, sahne["dates"][K])
    assert isinstance(z.value, RuntimeError)


def test_walk_forward_yuklemi_replaye_GECIRIR_yoksa_anahtari_HIC_gecirmez(sahne, monkeypatch):
    """Yüklemsiz çağrı yüzeyi BİREBİR eskisi: `durdurma` anahtarı replay'e hiç gitmez (sahte/casus replay'ler
    ve diğer çağıranlar — baseline/run/sprint — etkilenmez)."""
    yakalanan: list = []
    orj = backtest.replay

    def _casus(*a, **k):
        yakalanan.append(dict(k))
        return orj(*a, **k)

    monkeypatch.setattr(backtest, "replay", _casus)
    y = threading.Event().is_set
    _wf(sahne, durdurma=y)
    _wf(sahne)
    assert yakalanan[0].get("durdurma") is y, "walk_forward yüklemi replay'e İLETMEDİ"
    assert "durdurma" not in yakalanan[1], "yüklemsiz walk_forward replay'e `durdurma` anahtarı geçirdi"


def test_OLCUM_gun_basi_yuklem_maliyeti(sahne):
    """BEDEL YASASI — gün başı çağrının toplam replay süresine etkisi. İki ölçüm: (1) replay duvar saati
    yüklemsiz vs `Event.is_set` yüklemli (medyan, 5 tekrar — gürültülü, rapor için); (2) doğrudan birim maliyet
    × gün sayısı / replay süresi (gürültüsüz oran — hükmü bu verir)."""
    bayrak = threading.Event()

    def _sure(**kw) -> float:
        t0 = time.perf_counter()
        _replay(sahne, **kw)
        return time.perf_counter() - t0

    _replay(sahne)                                        # ısınma (ilk koşum önbellek/içe aktarma bedeli)
    yok = statistics.median(_sure() for _ in range(5))
    var = statistics.median(_sure(durdurma=bayrak.is_set) for _ in range(5))
    tekrar = N_BARS * 200
    t0 = time.perf_counter()
    for _ in range(tekrar):
        bayrak.is_set()
    birim = (time.perf_counter() - t0) / tekrar
    oran = birim * N_BARS / yok
    print(f"\n[v588 ÖLÇÜM] replay {N_BARS} gün: yüklemsiz medyan {yok * 1000:.1f} ms · yüklemli medyan "
          f"{var * 1000:.1f} ms · birim yüklem {birim * 1e9:.0f} ns · doğrudan oran {oran:.2e} "
          f"(gün başı maliyet {yok / N_BARS * 1000:.2f} ms)")
    assert oran < 0.01, f"yüklem maliyeti replay süresinin %{oran * 100:.2f}'i — gün başı tek çağrı ucuz olmalı"


# =================================================================================================
# B) ÖNBELLEK — durdurulan hesap yazılmaz
# =================================================================================================
def test_wf_cached_durdurmada_ONBELLEGE_ve_DISKE_YAZMAZ_bayraksiz_yazar(sahne):
    s = sahne
    y, _n = _sayac_sonra(50)
    with pytest.raises(backtest.ReplayDurduruldu):
        reflect._wf_cached(s["params"], 1, s["bars"], s["idx"], s["goal"], None, windows=s["w"], durdurma=y)
    assert reflect._INC_CACHE == {}, "yarım walk-forward süreç-içi önbelleğe yazıldı"
    assert not (config.STATE / reflect.INC_DISK_FILE).exists(), "yarım walk-forward diske yazıldı"
    # POZİTİF KONTROL: anahtar kilidi bırakıldı, aynı anahtar kurulmamış yüklemle hesaplanır ve YAZILIR
    reflect._wf_cached(s["params"], 1, s["bars"], s["idx"], s["goal"], None, windows=s["w"],
                       durdurma=lambda: False)
    assert len(reflect._INC_CACHE) == 1 and (config.STATE / reflect.INC_DISK_FILE).exists()


def test_probe_wf_durdurmada_ONBELLEGE_YAZMAZ(sahne):
    s = sahne
    aday = {"params": dict(s["params"], **{KNOB: 0.2}), "version": 2, "params_by_regime": {}}
    y, _n = _sayac_sonra(50)
    with pytest.raises(backtest.ReplayDurduruldu):
        reflect._probe_wf(aday, KNOB, 0.2, 1, s["bars"], s["idx"], s["goal"], s["w"], durdurma=y)
    assert reflect._PROBE_CACHE == {}, "yarım sonda walk-forward'ı önbelleğe yazıldı"
    assert not (config.STATE / reflect.PROBE_DISK_FILE).exists()


@pytest.mark.parametrize("kesilen", [None, 1])
def test_prefill_sirali_walk_forward_ORTASINDA_durdurma_beyanla_iner(sandbox_state, monkeypatch, kesilen):
    """Isınmanın incumbent ön-hesabı (sıralı yol): yüklem adımın walk-forward'ına da iletilir; ortasında
    fırlayan `ReplayDurduruldu` TSK-246'nın sıralı kesinti beyanıyla AYNI biçimde iner (istisna sızmaz,
    `durduruldu="sirali"`, olay `kalan` ile). POZİTİF KONTROL (`kesilen=None`): kurulmamış yüklemle üç
    varyant da hesaplanır."""
    goruldu: list = []

    def _wf(params, bars, index, goal, *a, **k):
        goruldu.append(k.get("durdurma"))
        if kesilen is not None and len(goruldu) == kesilen + 1:
            raise backtest.ReplayDurduruldu(tamamlanan_gun=2, toplam_gun=50, tarih="2024-01-03")
        return wf.wf_from_scores(0.10, folds=[(30, 0.2)] * 3, holdout=0.10)

    monkeypatch.setattr(reflect.backtest, "walk_forward", _wf)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    _onbellek_sifirla()
    y = lambda: False  # noqa: E731 — kurulmamış yüklem; kimliği iletimde ölçülür
    out = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"], durdurma=y)
    assert goruldu and all(g is y for g in goruldu), "sıralı walk-forward'a yüklem İLETİLMEDİ"
    if kesilen is None:
        assert out["computed"] == 3 and out["durduruldu"] is None, out
    else:
        assert out["computed"] == kesilen and out["durduruldu"] == "sirali", out
        olay = _olaylar("incumbent_prefill_durduruldu")
        assert olay and olay[-1]["kalan"] == 3 - kesilen and olay[-1]["tamamlanan_gun"] == 2, olay
        assert len(reflect._INC_CACHE) == kesilen, "yarım walk-forward önbelleğe yazıldı"
    _onbellek_sifirla()


# =================================================================================================
# C) SUBMIT — `_gate_eval` öncesi kontrol noktaları
# =================================================================================================
@pytest.fixture
def seeded(sandbox_state):
    from meridian import run
    _onbellek_sifirla()
    config.reload_config()
    run.bootstrap_v01()
    strat = config.default_strategy()
    strat["params"][KNOB] = SMALL
    config.dump_yaml(strat, config.strategy_path())
    versioning.snapshot(strat)
    yield sandbox_state
    _onbellek_sifirla()
    config.reload_config()


def _teklif(**ek) -> dict:
    return {"variable": KNOB, "new": FULL, "rationale": "v588 durdurma çivisi",
            "predicted_direction": "improve_oos_score", "predicted_delta": 0.05,
            "confidence": 0.5, "source": "deterministic", **ek}


class _SahteYuruyus:
    """Sahte walk-forward (v130 `_pass_gate` deseni): canlı sürüm → incumbent, diğer sürüm → aday. `gecen=True`
    aday kapıyı GEÇER; False ise geçmez. Her çağrıyı sayar, kwarg'ları saklar; `kanca(n, kwargs)` çağrı
    içinde koşar (bayrak kurmak ya da `ReplayDurduruldu` fırlatmak için)."""

    def __init__(self, monkeypatch, *, gecen: bool = True, kanca=None):
        hi = wf.wf_from_scores(0.30, folds=[(30, 0.6)] * 3, holdout=0.30)
        lo = wf.wf_from_scores(0.10, folds=[(30, 0.2)] * 3, holdout=0.10)
        self.inc, self.cand = (lo, hi) if gecen else (hi, lo)
        self.live = int(config.load_strategy().get("version", 1))
        self.n, self.kwargs, self.kanca = 0, [], kanca
        monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
        monkeypatch.setattr(backtest, "walk_forward", self)
        reflect._INC_CACHE.clear()

    def __call__(self, *a, **k):
        self.n += 1
        self.kwargs.append(dict(k))
        if self.kanca is not None:
            self.kanca(self.n, k)
        return copy.deepcopy(self.cand if int(k.get("strategy_version", self.live)) != self.live else self.inc)


def _defter_sabit(once: dict, sonra: dict) -> None:
    """İzinli dosyalar dışında HER ŞEY byte-byte aynı. `store`un yazım kilidi (`.locks/<ad>.lock`) izinli bir
    dosyanınsa izinlidir; bir DEFTERİN kilidi belirirse o deftere yazım DENENMİŞTİR — o da ihlal sayılır."""
    def _izinli(yol: str) -> bool:
        if yol.startswith(".locks/") and yol.endswith(".lock"):
            yol = yol[len(".locks/"):-len(".lock")]
        return yol in DEFTER_DISI
    fark = {y for y in _degisen(once, sonra) if not _izinli(y)}
    assert not fark, f"kesilen turda defter/durum dosyası DEĞİŞTİ: {sorted(fark)}"
    assert validation.ledger() == [], "K/aşınma (doğrulama) defterine satır düştü"
    assert memory.all_hypotheses() == [], "hipotez defterine satır düştü"


@pytest.mark.parametrize("k,asama,wf_sayisi", [
    (0, "giris", 0),              # bayrak submit'ten ÖNCE kurulu: guard bile koşmaz
    (1, "incumbent_oncesi", 0),   # guard geçti, pahalı hesap başlamadı
    (2, "aday_oncesi", 1),        # incumbent bitti, aday walk-forward'ı başlamadı
    (3, "kapi_oncesi", 2),        # iki walk-forward bitti — `_gate_eval` (K/aşınma yazımı) ÇAĞRILMADI
])
def test_submit_kontrol_noktasinda_bayrak_HICBIR_defter_satiri_yok(seeded, monkeypatch, k, asama, wf_sayisi):
    """ASIL ÇİVİ (karar A). Her kontrol noktası ayrı bir hücre: biri sökülünce bayrak bir SONRAKİ noktada
    görülür ve `asama`/walk-forward sayısı değişir — hücre kırmızıya döner."""
    sahte = _SahteYuruyus(monkeypatch)
    y, _n = _sayac_sonra(k)
    v0 = int(config.load_strategy()["version"])
    once = _foto(seeded)
    res = reflect.submit(_teklif(), config.goal(), durdurma=y)
    assert res["status"] == reflect.DURDURULDU_STATUS and res["sebep"] == reflect.DURDURMA_SEBEBI, res
    assert res["asama"] == asama and sahte.n == wf_sayisi, (res.get("asama"), sahte.n)
    assert int(config.load_strategy()["version"]) == v0, "kesilen turda sürüm arttı (ship)"
    _defter_sabit(once, _foto(seeded))
    olay = _olaylar("submit_durdurma_istegiyle_kesildi")
    assert olay and olay[-1]["asama"] == asama and len(str(olay[-1].get("detail", ""))) >= 20, olay


@pytest.mark.parametrize("kacinci,asama", [(1, "incumbent"), (2, "aday")])
def test_submit_walk_forward_ORTASINDA_durdurma_defter_yazmaz(seeded, monkeypatch, kacinci, asama):
    """Seçenek 1: TEK walk-forward da bölünür. Yüklem iki walk-forward'a da İLETİLİR; replay ortasında fırlayan
    `ReplayDurduruldu` submit'te yakalanır → beyanlı `durduruldu`, defter satırı YOK."""
    def _kanca(n, k):
        if n == kacinci:
            assert callable(k.get("durdurma")), f"{n}. walk-forward'a durdurma yüklemi İLETİLMEDİ"
            raise backtest.ReplayDurduruldu(tamamlanan_gun=5, toplam_gun=100, tarih="2024-01-08")

    sahte = _SahteYuruyus(monkeypatch, kanca=_kanca)
    once = _foto(seeded)
    res = reflect.submit(_teklif(), config.goal(), durdurma=lambda: False)
    assert res["status"] == reflect.DURDURULDU_STATUS and res["asama"] == asama, res
    assert sahte.n == kacinci
    _defter_sabit(once, _foto(seeded))
    olay = _olaylar("submit_durdurma_istegiyle_kesildi")[-1]
    assert (olay["asama"], olay["tamamlanan_gun"], olay["toplam_gun"]) == (asama, 5, 100), olay


def _norm(x):
    """İkiz kıyası için zaman damgalarını maskeler (içerik aynı, saat farklı olabilir)."""
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_norm(v) for v in x]
    if isinstance(x, str) and re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", x):
        return "<ts>"
    return x


def _ikiz_kur(monkeypatch, kok: Path) -> Path:
    """`seeded` ile AYNI tohum, AYRI bir kum havuzunda (bayraklı/bayraksız koşum birbirinin defterini görmesin)."""
    from meridian import run
    st = kok / "state"
    (st / "history").mkdir(parents=True)
    (st / "bars").mkdir(parents=True)
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(REPO / "state" / f, st / f)
    monkeypatch.setattr(config, "STATE", st)
    monkeypatch.setattr(config, "HISTORY", st / "history")
    monkeypatch.setattr(config, "BARS", st / "bars")
    _onbellek_sifirla()
    config.reload_config()
    run.bootstrap_v01()
    strat = config.default_strategy()
    strat["params"][KNOB] = SMALL
    config.dump_yaml(strat, config.strategy_path())
    versioning.snapshot(strat)
    return st


def _defter_ozeti(st: Path) -> dict:
    return {"hyp": _norm(store.read_jsonl("hypotheses.jsonl")),
            "val": _norm(store.read_jsonl(validation.LEDGER_FILE)),
            "erozyon": _norm(store.read_json("oos_erosion.json", None)),
            "karne": _norm(store.read_json("scoreboard.json", None)),
            "strateji": (st / "strategy.yaml").read_text(encoding="utf-8"),
            "gecmis": sorted(p.name for p in (st / "history").iterdir())}


@pytest.mark.parametrize("senaryo", ["submit_ship", "arama_ship", "arama_kuraklik"])
def test_POZITIF_KONTROL_bayrak_kurulmamisken_defterler_ve_sonuc_BIREBIR(sandbox_state, monkeypatch, tmp_path,
                                                                         senaryo):
    """Yüklem VERİLİP hiç kurulmazsa sonuç ve TÜM defterler yüklemsiz koşumla BİREBİR (ikiz kum havuzu).
    Üç yol: doğrudan submit → ship · arama → submit → ship · arama → kazanan yok → oturum kaydı."""
    ozet = {}
    for ad, kw in (("yuklemsiz", {}), ("yuklemli", {"durdurma": lambda: False})):
        st = _ikiz_kur(monkeypatch, tmp_path / ad)
        sahte = _SahteYuruyus(monkeypatch, gecen=(senaryo != "arama_kuraklik"))
        if senaryo == "submit_ship":
            res = reflect.submit(_teklif(), config.goal(), **kw)
        else:
            res = reflect.search_and_submit(None, None, config.goal(), windows=None, k_max=1, budget=3, **kw)
        ozet[ad] = {"res": _norm(json.loads(_parmak(res))), "defter": _defter_ozeti(st), "wf": sahte.n}
    beklenen = {"submit_ship": "shipped", "arama_ship": "shipped", "arama_kuraklik": "no_clearing_candidate"}
    assert ozet["yuklemsiz"]["res"]["status"] == beklenen[senaryo], ozet["yuklemsiz"]["res"]
    if senaryo == "arama_kuraklik":
        assert len(ozet["yuklemsiz"]["defter"]["val"]) == 1, "kuraklık oturumu resmî kaydını düşürmedi (kıyas boş)"
    assert ozet["yuklemli"] == ozet["yuklemsiz"], "kurulmamış yüklem sonucu/defterleri DEĞİŞTİRDİ"


# =================================================================================================
# D) ARAMA — search_and_submit yüklemi iletir; kesilen arama submit etmez, oturum kaydı yazmaz
# =================================================================================================
def test_search_and_submit_yuklemi_ILETIR_bayrakla_arama_iner(seeded, monkeypatch):
    """KIRMIZI BAŞLAR: `search_and_submit` durdurma yüklemini hiç almıyordu — reflect_once yolunda arama
    durdurmayla ASLA kesilmiyordu (tasarım §1)."""
    sahte = _SahteYuruyus(monkeypatch)
    once = _foto(seeded)
    res = reflect.search_and_submit(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                    durdurma=lambda: True)
    assert res["status"] == reflect.DURDURULDU_STATUS and res["asama"] == "arama", res
    assert sahte.n == 0, f"bayrak kuruluyken {sahte.n} walk-forward koştu"
    _defter_sabit(once, _foto(seeded))


def test_kesilen_aramada_KAZANAN_varken_SUBMIT_EDILMEZ(seeded, monkeypatch):
    """Arama bir kazanan buldu (sonda 1 kapıyı geçti), sonra bayrak kuruldu → kazanan submit'e GİTMEZ (kesilen
    tur ship etmez), `asama` "arama" (submit'in giriş noktası değil — iki savunma hattı ayrı ölçülür)."""
    sahte = _SahteYuruyus(monkeypatch, gecen=True)
    once = _foto(seeded)
    res = reflect.search_and_submit(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                    durdurma=lambda: sahte.n >= 2)
    assert res["search"]["best"] is not None, "sahne kazanan üretmedi — çivi ölçüm yapamaz"
    assert res["search"]["sebep"] == reflect.DURDURMA_SEBEBI and res["search"]["evaluated"] == 1
    assert res["status"] == reflect.DURDURULDU_STATUS and res["asama"] == "arama", res
    _defter_sabit(once, _foto(seeded))


def test_kesilen_aramada_kazanan_YOKKEN_oturum_kaydi_YAZILMAZ(seeded, monkeypatch):
    """Kazanan yokken arama oturumun TEK resmî kaydını kendisi düşürür (`record_session`). Kesilen oturum bir
    soru SORMADI sayılır: resmî kayıt (K/aşınma satırı) yazılmaz. Kesilmeseydi yazılırdı (ikiz pozitif kontrol:
    `test_POZITIF_KONTROL_…[arama_kuraklik]`)."""
    sahte = _SahteYuruyus(monkeypatch, gecen=False)
    once = _foto(seeded)
    res = reflect.search_and_submit(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                    durdurma=lambda: sahte.n >= 2)
    s = res["search"]
    assert s["evaluated"] == 1 and s["best"] is None and s["sebep"] == reflect.DURDURMA_SEBEBI, s
    assert s["oturum_kaydi"] is None
    assert res["status"] == reflect.DURDURULDU_STATUS
    _defter_sabit(once, _foto(seeded))


@pytest.mark.parametrize("kacinci", [1, 3])
def test_arama_walk_forward_ORTASINDA_durdurma_muhasebe_TUTAR(seeded, monkeypatch, kacinci):
    """Replay ortasında fırlayan `ReplayDurduruldu`: incumbent'ta (1. çağrı) → plan kurulmadı, sayılar None;
    ikinci sondada (3. çağrı) → yarım sonda DEĞERLENDİRİLMEDİ: `kalan + evaluated + atlanan = planlanan`,
    `fresh`/`cached_hits` negatif/şişkin değil, yarım sonda `tried`e yazılmadı, oturum kaydı yok."""
    def _kanca(n, k):
        if n == kacinci:
            assert callable(k.get("durdurma")), f"{n}. walk-forward'a yüklem İLETİLMEDİ"
            raise backtest.ReplayDurduruldu(tamamlanan_gun=3, toplam_gun=100, tarih="2024-01-05")

    _SahteYuruyus(monkeypatch, gecen=False, kanca=_kanca)
    tried: set = set()
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                            tried=tried, durdurma=lambda: False)
    assert res["kesildi"] is True and res["sebep"] == reflect.DURDURMA_SEBEBI, res
    assert validation.ledger() == [], "kesilen arama resmî oturum kaydı düşürdü"
    if kacinci == 1:
        assert res["planlanan_sonda"] is None and res["kalan_sonda"] is None and res["evaluated"] == 0
        assert res["incumbent_oos"] is None
    else:
        assert res["planlanan_sonda"] == 3 and res["evaluated"] == 1, res
        assert res["kalan_sonda"] + res["evaluated"] + res["skipped_wallclock"] == res["planlanan_sonda"]
        assert (res["fresh"], res["cached_hits"]) == (1, 0), (res["fresh"], res["cached_hits"])
        assert len(tried) == 1, f"yarım sonda `tried`e yazıldı: {tried}"
    olay = _olaylar("search_durdurma_istegiyle_kesildi")[-1]
    assert (olay["tamamlanan_gun"], olay["toplam_gun"], olay["kesilen_gun"]) == (3, 100, "2024-01-05"), olay


# =================================================================================================
# E) HERMES — yansıma turu zinciri
# =================================================================================================
def test_reflect_once_oneri_turu_kesilince_ARAMAYA_DUSULMEZ(seeded, monkeypatch):
    """Öneri submit'te `_gate_eval` öncesinde kesildi → reflect_once aramaya DÜŞMEZ (düşseydi kesilen tur yeni
    bir arama başlatırdı), sonucu aynen döner; hiçbir defter satırı yok."""
    bayrak = threading.Event()
    _SahteYuruyus(monkeypatch, kanca=lambda n, k: bayrak.set() if n == 2 else None)
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: _teklif(source="llm"))
    monkeypatch.setattr(reflect, "search_and_submit",
                        lambda *a, **k: pytest.fail("kesilen öneri turu aramaya düştü"))
    once = _foto(seeded)
    res = hermes.reflect_once(target_regime="trend_up", durdurma=bayrak.is_set)
    assert res["status"] == reflect.DURDURULDU_STATUS and res["asama"] == "kapi_oncesi", res
    _defter_sabit(once, _foto(seeded))


def test_reflect_once_yuklemi_arama_zincirine_ILETIR_yoksa_anahtar_YOK(sandbox_state, monkeypatch):
    """Yüklem verilirse `search_and_submit`e AYNI nesne iletilir; verilmezse anahtar hiç geçmez (eski çağrı
    yüzeyi — `lambda *a, **k` olmayan sahteler ve hermes.loop/tmux yolu etkilenmez)."""
    gorulen: list = []
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: None)
    monkeypatch.setattr(hermes, "VIRGIN_FALLBACK", False)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.setattr(reflect, "search_and_submit",
                        lambda *a, **k: gorulen.append(dict(k)) or {"status": "no_clearing_candidate", "search": {}})
    y = threading.Event().is_set
    hermes.reflect_once(target_regime="trend_up", durdurma=y)
    hermes.reflect_once(target_regime="trend_up")
    assert gorulen[0].get("durdurma") is y, "reflect_once yüklemi aramaya İLETMEDİ"
    assert "durdurma" not in gorulen[1]


def test_reflect_once_girisinde_bayrak_LLM_cagrilmaz_ilerleme_asili_kalmaz(sandbox_state, monkeypatch):
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: pytest.fail("bayrak kuruluyken LLM'e gidildi"))
    res = hermes.reflect_once(target_regime="trend_up", durdurma=lambda: True)
    assert res["status"] == reflect.DURDURULDU_STATUS and res["asama"] == "giris", res
    assert not hermes.SEARCH_PROGRESS.get("running")


def test_kesilen_arama_ilerlemesi_DURDURULDU_fazinda_iner(sandbox_state, monkeypatch):
    """Pano ilerlemesi kesilen aramayı "done" diye göstermez: `phase="durduruldu"`, `running=False`."""
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: None)
    monkeypatch.setattr(hermes, "VIRGIN_FALLBACK", False)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.setattr(reflect, "search_and_submit",
                        lambda *a, **k: {"status": reflect.DURDURULDU_STATUS, "sebep": reflect.DURDURMA_SEBEBI,
                                         "asama": "arama", "search": {"evaluated": 1, "cleared": 0}})
    res = hermes.reflect_once(target_regime="trend_up", durdurma=lambda: False)
    assert res["status"] == reflect.DURDURULDU_STATUS
    assert hermes.SEARCH_PROGRESS.get("running") is False and hermes.SEARCH_PROGRESS.get("phase") == "durduruldu"


# =================================================================================================
# F) HERMES_RUNTIME — kesilen tur SAYILMAZ
# =================================================================================================
TABAN = 6
CANLI = "trend_up"


class _Durdurucu:
    """`hr._stop` yerine: `kur()` bayrağı koyar; `wait` (tur sonu) döngüyü bitirir (bekleme yok)."""

    def __init__(self):
        self._dur = False

    def kur(self) -> None:
        self._dur = True

    def is_set(self) -> bool:
        return self._dur

    def wait(self, _s=None) -> bool:
        self._dur = True
        return True


def _islem(rejim: str, gun: str) -> dict:
    return {"regime": rejim, "ts_close": gun, "r_multiple": 0.1}


def _dongu_kur(monkeypatch, *, canli_vade: bool, bg: bool = False) -> None:
    """Bekleme döngüsünün DIŞ yüzeyleri sahte (sağlık, öz-onarım, nabız); dal seçimi, vade yüklemi, `_record` ve
    tabanlar GERÇEK. `_persist` sadeleşir: `_state`i STATUS_FILE'a aynen yazar (beyin ölçümü konu değil)."""
    monkeypatch.setattr(hr, "_state", {"reflections": 0, "last_reflection": None, "last_result": None,
                                       "last_variable": None, "last_reflect_at": None})
    monkeypatch.setattr(hr, "_thread", None)
    monkeypatch.setattr(hr, "_acilis_senkron_calisti", True)
    monkeypatch.setattr(hr, "_persist", lambda: store.write_json(hr.STATUS_FILE, dict(hr._state)))
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: {})
    monkeypatch.setattr(hermes, "config_ensure_integrations", lambda: {})
    monkeypatch.setattr(watchdog, "beat", lambda _ad: None)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(health, "stale", lambda *_a, **_k: False)
    monkeypatch.setattr(health, "learn_halted", lambda: False)
    monkeypatch.setenv("MERIDIAN_BG_REFLECT", "1" if bg else "0")
    monkeypatch.setenv("MERIDIAN_WARMUP_SPRINTS", "0")
    eski = [_islem("trend_down", f"2025-{m:02d}-15") for m in range(1, 1 + TABAN)]
    yeni = ([_islem(CANLI, str(dt.date(2026, 1, 1) + dt.timedelta(days=15 * i))) for i in range(6)]
            if canli_vade else [])
    store.write_jsonl("trades.jsonl", eski + yeni)
    store.write_json("regime.json", {"regime": CANLI})
    store.write_json(hr.STATUS_FILE, {"last_reflect_at": TABAN})


def test_run_kesilen_CANLI_tur_SAYILMAZ_uctan_uca(seeded, monkeypatch):
    """UÇTAN UCA (gerçek `reflect_once` → gerçek `submit`, sahte walk-forward): bayrak aday walk-forward'ı
    sırasında kurulur (SIGTERM benzetimi) → `_gate_eval` öncesi kesilir. `_record` İŞLEMEZ: `last_reflect_at`,
    `reflections`, `last_result` sabit; durum dosyası tutarlı; defterlerde satır yok; beyanlı olay düşer."""
    _dongu_kur(monkeypatch, canli_vade=True)
    dur = _Durdurucu()
    monkeypatch.setattr(hr, "_stop", dur)
    _SahteYuruyus(monkeypatch, kanca=lambda n, k: dur.kur() if n == 2 else None)
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: _teklif(source="llm"))
    once = _foto(seeded)
    hr._run(poll_seconds=1)
    assert hr._state["last_reflect_at"] == TABAN, "kesilen tur canlı geri sayımı İLERLETTİ"
    assert hr._state["reflections"] == 0 and hr._state["last_result"] is None, hr._state
    assert store.read_json(hr.STATUS_FILE, {}).get("last_reflect_at") == TABAN, "durum dosyası tabanı kaydı"
    _defter_sabit(once, _foto(seeded))
    olay = _olaylar("yansima_turu_sayilmadi")
    assert olay and olay[-1]["arka_plan"] is False and olay[-1]["asama"] == "kapi_oncesi", olay
    assert len(str(olay[-1].get("detail", ""))) >= 20


def test_POZITIF_KONTROL_run_bayraksiz_canli_tur_SAYILIR(seeded, monkeypatch):
    """Aynı kurulum, bayrak hiç kurulmaz: tur ship eder, `_record` koşar, taban defter uzunluğuna ilerler."""
    _dongu_kur(monkeypatch, canli_vade=True)
    monkeypatch.setattr(hr, "_stop", _Durdurucu())
    _SahteYuruyus(monkeypatch)
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: _teklif(source="llm"))
    hr._run(poll_seconds=1)
    n = len(store.read_jsonl("trades.jsonl"))
    assert hr._state["last_result"] == "shipped" and hr._state["reflections"] == 1, hr._state
    assert hr._state["last_reflect_at"] == n and store.read_json(hr.STATUS_FILE, {})["last_reflect_at"] == n
    assert not _olaylar("yansima_turu_sayilmadi")


@pytest.mark.parametrize("kesildi", [True, False])
def test_run_ARKA_PLAN_turu_kesilince_rejim_tabani_SABIT(sandbox_state, monkeypatch, kesildi):
    """Arka plan turu da aynı yasayla: kesilirse `bg_reflect_by_regime[rejim]` ilerlemez, `_record` işlemez.
    Çağrı yeri yüklemi (`_stop.is_set`) İLETİR. Pozitif kontrol: kesilmeyen tur tabanı ilerletir."""
    _dongu_kur(monkeypatch, canli_vade=False, bg=True)
    dur = _Durdurucu()
    monkeypatch.setattr(hr, "_stop", dur)
    gorulen: list = []

    def _sahte(target_regime="auto", *, background=False, durdurma=None):
        gorulen.append({"rejim": target_regime, "bg": background, "durdurma": durdurma})
        if kesildi:
            return {"status": reflect.DURDURULDU_STATUS, "sebep": reflect.DURDURMA_SEBEBI, "asama": "arama"}
        return {"status": "rejected_by_backtest", "hypothesis": {"variable": f"x@{target_regime}"}}

    monkeypatch.setattr(hermes, "reflect_once", _sahte)
    hr._run(poll_seconds=1)
    assert [(g["rejim"], g["bg"]) for g in gorulen] == [("trend_down", True)], gorulen
    assert gorulen[0]["durdurma"] == dur.is_set, "arka plan turu `_stop.is_set` yüklemini ALMADI"
    if kesildi:
        assert "trend_down" not in (hr._state.get("bg_reflect_by_regime") or {}), hr._state
        assert hr._state["reflections"] == 0
        assert _olaylar("yansima_turu_sayilmadi")[-1]["arka_plan"] is True
    else:
        assert hr._state["bg_reflect_by_regime"]["trend_down"] == TABAN and hr._state["reflections"] == 1


@pytest.mark.parametrize("kesildi", [True, False])
def test_ELLE_istek_turu_kesilince_istek_KALIR_taban_SABIT(sandbox_state, monkeypatch, kesildi):
    """Pano isteği öğrenme sürecinde (`_yansima_istegini_isle`) koşar. Kesilirse: `_record` işlemez, istek dosyası
    SİLİNMEZ (SIGKILL'deki beyanla aynı: yeniden başlayan döngü isteği koşar — operatörün isteği kaybolmaz),
    kayıt `durduruldu`. Pozitif kontrol: kesilmeyen istek silinir, kayıt `bitti`, taban ilerler."""
    _dongu_kur(monkeypatch, canli_vade=True)
    hr._state.update(poll_seconds=300, last_reflect_at=TABAN)
    dur = threading.Event()
    monkeypatch.setattr(hr, "_stop", dur)
    gorulen: list = []

    def _sahte(target_regime="auto", *, background=False, durdurma=None):
        gorulen.append(durdurma)
        if kesildi:
            return {"status": reflect.DURDURULDU_STATUS, "sebep": reflect.DURDURMA_SEBEBI, "asama": "aday"}
        return {"status": "rejected_by_backtest", "hypothesis": {"variable": KNOB}}

    monkeypatch.setattr(hermes, "reflect_once", _sahte)
    store.write_json(hr.YANSIMA_ISTEGI_FILE, {"istek_id": "v588", "istek_at": hr._now(), "kaynak": "v588"})
    assert hr._yansima_istegini_isle() is True
    assert gorulen and gorulen[0] == dur.is_set, "elle istek turu `_stop.is_set` yüklemini ALMADI"
    kayit = hr._state["son_elle_istek"]
    if kesildi:
        assert store.read_json(hr.YANSIMA_ISTEGI_FILE, None) is not None, "kesilen istek SİLİNDİ — kaybolur"
        assert kayit["durum"] == "durduruldu" and hr._state["last_reflect_at"] == TABAN, (kayit, hr._state)
        assert hr._state["reflections"] == 0
    else:
        assert store.read_json(hr.YANSIMA_ISTEGI_FILE, None) is None
        assert kayit["durum"] == "bitti" and hr._state["last_reflect_at"] == len(store.read_jsonl("trades.jsonl"))


class _EsZamanliIplik:
    """`reflect_now`un arka plan ipliği yerine (v560 deseni): `start()` hedefi AYNI iş parçacığında koşar."""

    def __init__(self, target=None, name=None, daemon=None, **_k):
        self._hedef = target

    def start(self) -> None:
        self._hedef()


def test_reflect_now_yolu_YUKLEM_GECIRMEZ(sandbox_state, monkeypatch):
    """`reflect_now` (süreç-içi/CLI) döngüsüz koşabilir; o an `_stop` bir ÖNCEKİ `stop()`tan kurulu kalmış
    olabilir — yüklem geçseydi elle yansıma daha başlamadan "kesilirdi". Gövde yüklemsiz çağrılır, tur sayılır."""
    _dongu_kur(monkeypatch, canli_vade=True)
    hr._state["last_reflect_at"] = TABAN
    dur = threading.Event()
    dur.set()                                  # döngü önceden durdurulmuş
    monkeypatch.setattr(hr, "_stop", dur)
    monkeypatch.setattr(hr, "threading", types.SimpleNamespace(Thread=_EsZamanliIplik))
    gorulen: list = []
    monkeypatch.setattr(hermes, "reflect_once",
                        lambda *a, **k: gorulen.append(dict(k)) or {"status": "rejected_by_backtest"})
    out = hr.reflect_now()
    assert out["status"] == "started", out
    assert gorulen == [{}], f"reflect_now yansımaya yüklem geçirdi: {gorulen}"
    assert hr._state["reflections"] == 1 and hr._state["last_reflect_at"] == len(store.read_jsonl("trades.jsonl"))


# =================================================================================================
# F') ÖLÇÜM — SIGTERM'den yansıma turunun inişine (gerçek replay)
# =================================================================================================
def test_OLCUM_sigtermden_yansima_turu_inisine_sure_30_sn_ALTINDA(seeded, sahne, monkeypatch):
    """HEDEF ÖLÇÜMÜ (tasarım §3): bekleme döngüsü canlı bir yansıma turunda, incumbent walk-forward'ı GERÇEK
    replay'le hesaplarken SIGTERM kancası tetiklenir. Replay günü yapay olarak yavaş (gün başı ~20 ms, tek
    walk-forward ≈ 4 sn): yüklem okunmasaydı tur iki tam walk-forward + kapı sürerdi (> 8 sn). Beklenen iniş ≈
    bir replay günü. Tur SAYILMAZ, defterlere satır düşmez."""
    _dongu_kur(monkeypatch, canli_vade=True)
    bayrak = threading.Event()
    monkeypatch.setattr(hr, "_stop", bayrak)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (sahne["bars"], sahne["idx"]))
    monkeypatch.setattr(reflect, "_default_windows", lambda: sahne["w"])
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: _teklif(source="llm"))
    # İPLİK ÖMRÜ SINIRI — YALNIZ çivi kırmızıyken önemli (ölçülen yolu etkilemez): yüklem okunmasaydı tur
    # öneriden sonra aramaya düşer ve sahnede sonda başına ~4 sn'lik walk-forward'lar koşardı. Arama 1 sondaya
    # kısılır ki kırmızı koşumda iplik join penceresinde BİTSİN — bitmeyen daemon iplik monkeypatch geri
    # alındıktan sonra GERÇEK `state/`e yazar (ilk kırmızı koşumda ölçüldü: çalışma ağacının state/'ine
    # events/probe_cache/search_progress düştü, 2026-09-28).
    monkeypatch.setattr(hermes, "search_budget", lambda: {"tavan": 1, "kaynak": "v588", "formul": "v588"})
    monkeypatch.setattr(hermes, "SEARCH_KMAX", 1)
    ilk_gun = threading.Event()
    orj = backtest.regime_mod.build_regime_json

    def _yavas_gun(*a, **k):
        ilk_gun.set()
        time.sleep(0.02)
        return orj(*a, **k)

    monkeypatch.setattr(backtest.regime_mod, "build_regime_json", _yavas_gun)
    once = _foto(seeded)
    iplik = threading.Thread(target=hr._run, args=(1,), name="v588-olcum", daemon=True)
    iplik.start()
    try:
        assert ilk_gun.wait(20), "yansıma turu replay'e girmedi — ölçüm zemini yok"
        t0 = time.monotonic()
        learn_run._isaret(signal.SIGTERM, None)
        iplik.join(timeout=40)
        gecen = time.monotonic() - t0
    finally:
        bayrak.set()
        iplik.join(timeout=120)             # kırmızıda bile iplik kum havuzu geri alınmadan İNSİN
    assert not iplik.is_alive(), "döngü inmedi"
    assert gecen <= 2.0, f"iniş {gecen:.2f} sn — beklenen ≈ bir replay günü (yüklem gün başında okunmuyor)"
    assert gecen <= 30.0
    assert hr._state["last_reflect_at"] == TABAN and hr._state["reflections"] == 0, hr._state
    _defter_sabit(once, _foto(seeded))
    olay = _olaylar("yansima_turu_sayilmadi")
    assert olay and olay[-1]["asama"] == "incumbent", olay
    print(f"\n[v588 ÖLÇÜM] SIGTERM kancası → yansıma turu inişi: {gecen:.3f} sn (gerçek replay, yapay gün ~20 ms)")


# =================================================================================================
# G) SÖZLEŞME — yüklem ENJEKTE edilir
# =================================================================================================
def _import_kenarlari(dosya: str, hedefler: tuple[str, ...]) -> list[tuple[int, str | None]]:
    """(satır, kapsayan fonksiyon) — fonksiyon-içi import'lar da sayılır (import-linter onları da kenar sayar)."""
    agac = ast.parse((REPO / "meridian" / dosya).read_text(encoding="utf-8"))
    kenar: list = []

    def _gez(dugum, fn):
        for c in ast.iter_child_nodes(dugum):
            yeni_fn = c.name if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
            if isinstance(c, ast.ImportFrom):
                adlar = [a.name for a in c.names]
                if any((c.module or "").endswith(h) or h in adlar for h in hedefler):
                    kenar.append((c.lineno, fn))
            elif isinstance(c, ast.Import):
                if any(a.name.endswith(h) for a in c.names for h in hedefler):
                    kenar.append((c.lineno, fn))
            _gez(c, yeni_fn)
    _gez(agac, None)
    return kenar


def test_import_sozlesmesi_yuklem_ENJEKTE_edilir():
    """`backtest` yukarı katmanları (reflect/hermes/hermes_runtime) tanımaz; `reflect` `hermes_runtime`i tanımaz
    (v586 ile aynı ölçüm); `hermes`in `hermes_runtime` kenarı ÖLÇÜLDÜ (2026-09-28): yalnız tmux bekleme
    döngüsünde (`loop`, iki fonksiyon-içi import) — yansıma zinciri (`reflect_once`/`_reflect_once_govde`) bu
    kenarı KULLANMAZ, yüklem çağırandan gelir."""
    assert _import_kenarlari("backtest.py", ("reflect", "hermes", "hermes_runtime")) == []
    assert _import_kenarlari("reflect.py", ("hermes_runtime",)) == []
    hermes_kenar = _import_kenarlari("hermes.py", ("hermes_runtime",))
    assert hermes_kenar and {fn for _l, fn in hermes_kenar} == {"loop"}, hermes_kenar

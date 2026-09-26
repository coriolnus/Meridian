"""test_yansima_taban_v560.py — TSK-227: arka plan yansıması canlı rejimin geri sayımını (`last_reflect_at`) SIFIRLAMAZ.

KUSUR (TSK-204 uygulayıcısı + Sonnet incelemesi kod okumasıyla doğruladı; ilk kaydı `docs/SISTEM-DENETIMI-2026-08-02.md`
[ş2]): `hermes_runtime._record` HER yansıma türünde (canlı · arka plan · elle) TEK paylaşımlı `_state["last_reflect_at"]`ı
güncel defter uzunluğuna çekiyordu. Bu alan canlı rejimin vade yüklemi `_yansima_vadesi`nin (TSK-204) TEK zaman tabanı ve
bekçinin ÖĞRENME DURDU alarmının (A) ayağının (`yansima_kapisi`) tabanıdır. Canlı sayaç `reflection_every`e ulaşmadan araya
giren her arka plan yansıması sayacı sıfırlıyordu → sık arka plan yansımasında canlı yansıma HİÇ ateşlemez (livelock), (A)
da vadeyi hiç görmez (körleşir). A1 ölçümü (Rol-1, 2026-09-26): `bg_reflection_start` 71 kez, sonuncusu 2026-08-16,
09-25'ten beri 0 — risk bugün etkin değil.

KARAR (Rol-1, 2026-09-26): `last_reflect_at` YALNIZ canlı-rejim ve ELLE (`reflect_now`) yansımada taşınır; arka plan
yansıması yalnız kendi rejim tabanını (`bg_reflect_by_regime[rejim]`) taşır. `_record(res, *, arka_plan)` — parametre
ZORUNLU ve ADIYLA verilir: varsayılanı olsaydı yarın eklenecek bir arka plan yolu beyansız çağrıyla canlı tabanı yine
sessizce taşırdı (bu kusurun sınıfı).

ÇİVİLER BEKLEME DÖNGÜSÜNÜ (`_run`) GERÇEKTEN KOŞTURUR: yansıma sahtedir, tur sayısı `_AdimliDurdurucu` ile sınırlıdır
(bekleme yok — `wait` sıradaki adımı koşar). Böylece yalnız `_record` değil, ÇAĞRI YERİNDEKİ beyan da ölçülür.
"""
from __future__ import annotations

import ast
import datetime as dt
import inspect
import types

import pytest

from meridian import config, health, hermes, store, watchdog
from meridian import hermes_runtime as hr

CANLI = "trend_up"      # duraklatılmış rejim (chop) DEĞİL — K1 duraklatması tartışmaya bulaşmasın
TABAN = 18              # biriktirilmiş defterin uzunluğu = son canlı yansımanın tabanı (hermes_status.json)


class _AdimliDurdurucu:
    """`hr._stop` yerine geçer: her `wait` (tur sonu) sıradaki adımı koşar; adım kalmayınca döngüyü durdurur.
    Tur sayısı = adım sayısı + 1. Gerçek bekleme YOKTUR (`poll_seconds` yok sayılır)."""

    def __init__(self, adimlar):
        self._adimlar = list(adimlar)
        self._dur = False

    def is_set(self) -> bool:
        return self._dur

    def wait(self, _saniye=None) -> bool:
        if self._adimlar:
            self._adimlar.pop(0)()
        else:
            self._dur = True
        return self._dur


class _EsZamanliIplik:
    """`reflect_now`un arka plan ipliği yerine: `start()` hedefi AYNI iş parçacığında koşar (bekleme yok)."""

    def __init__(self, target=None, name=None, daemon=None, **_k):
        self._hedef = target

    def start(self) -> None:
        self._hedef()


def _islem(rejim: str, gun: str) -> dict:
    return {"regime": rejim, "ts_close": gun, "r_multiple": 0.1}


def _birikmis() -> list[dict]:
    """TABAN uzunluğunda birikmiş defter: iki canlı-dışı rejimin ufku DOLU kanıtı (arka plan adayları).
    trend_down 10 işlem (9 ay) > high_vol 8 işlem (7 ay) → seçici önce trend_down'u, sonra high_vol'u seçer."""
    td = [_islem("trend_down", f"2025-{m:02d}-15") for m in range(1, 11)]
    hv = [_islem("high_vol", f"2025-{m:02d}-20") for m in range(1, 9)]
    assert len(td) + len(hv) == TABAN
    return td + hv


def _canli(i: int) -> dict:
    """Canlı rejimde i. yeni kapanış — 15 gün arayla (every=5 → 60 gün yayılım ≥ 30 günlük takvim tabanı)."""
    return _islem(CANLI, str(dt.date(2026, 1, 1) + dt.timedelta(days=15 * i)))


def _every() -> int:
    every = int(config.goal()["reflection_every"])
    assert every >= 3, f"senaryo reflection_every ≥ 3 varsayar (ölçülen {every})"
    return every


def _kur(n_canli: int) -> None:
    """Defter = birikmiş + `n_canli` canlı kapanış; canlı rejim `CANLI`; kalıcı taban `TABAN`."""
    store.write_jsonl("trades.jsonl", _birikmis() + [_canli(i) for i in range(n_canli)])
    store.write_json("regime.json", {"regime": CANLI})
    store.write_json(hr.STATUS_FILE, {"last_reflect_at": TABAN})


def _kapanis_ekle(i: int) -> None:
    store.append_jsonl("trades.jsonl", _canli(i))


def _defter_n() -> int:
    return len(store.read_jsonl("trades.jsonl"))


@pytest.fixture
def dongu(sandbox_state, monkeypatch):
    """Bekleme döngüsünü sahte yansımayla koşturan kurulum → `(kos, cagrilar)`.

    Sahte olan yalnız DIŞ yüzeylerdir (yansımanın kendisi, sağlık bayrakları, öz-onarım eşitlemeleri, nabız, beyin
    ölçümlü durum yazımı); dal seçimi, `_bg_ready_regime`, `_yansima_vadesi`, `_record` ve taban güncellemesi GERÇEKTİR."""
    monkeypatch.setattr(hr, "_state", {"reflections": 0, "last_reflection": None, "last_result": None,
                                       "last_variable": None, "last_reflect_at": None})
    monkeypatch.setattr(hr, "_thread", None)
    monkeypatch.setattr(hr, "_acilis_senkron_calisti", True)       # açılış senkronu alt süreç koşturur — konu değil
    monkeypatch.setattr(hr, "_persist", lambda: None)                # beyin/zincir ölçümlü yazım — konu değil
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: {})
    monkeypatch.setattr(hermes, "config_ensure_integrations", lambda: {})
    monkeypatch.setattr(watchdog, "beat", lambda _ad: None)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(health, "stale", lambda *_a, **_k: False)
    monkeypatch.setattr(health, "learn_halted", lambda: False)
    monkeypatch.setenv("MERIDIAN_BG_REFLECT", "1")
    monkeypatch.setenv("MERIDIAN_WARMUP_SPRINTS", "0")              # ısınma dalı bu çivinin konusu değil
    cagrilar: list[dict] = []

    def _sahte_yansima(target_regime="auto", *, background=False):
        cagrilar.append({"rejim": target_regime, "arka_plan": background, "defter": _defter_n()})
        return {"status": "rejected_by_backtest", "hypothesis": {"variable": f"exit.trail_atr_mult@{target_regime}"}}

    monkeypatch.setattr(hermes, "reflect_once", _sahte_yansima)

    def kos(adimlar=()):
        monkeypatch.setattr(hr, "_stop", _AdimliDurdurucu(adimlar))
        hr._run(poll_seconds=1)
        # `_run` her istisnayı `last_result = "error: …"` olarak yutar — kurulum hatası yeşil görünmesin.
        assert not str(hr._state.get("last_result") or "").startswith("error"), hr._state.get("last_result")

    return kos, cagrilar


# =================================================================================================
# (1) ARKA PLAN YANSIMASI canlı tabanı TAŞIMAZ, kendi rejim tabanını TAŞIR
# =================================================================================================
def test_1_arka_plan_yansimasi_canli_tabani_TASIMAZ_kendi_tabanini_TASIR(dongu):
    kos, cagrilar = dongu
    every = _every()
    _kur(every - 2)                                   # canlı sayaç every-2: vade dolmadı → arka plan dalı
    n = _defter_n()
    kos()
    assert cagrilar == [{"rejim": "trend_down", "arka_plan": True, "defter": n}], cagrilar
    assert hr._state["last_reflect_at"] == TABAN, \
        "arka plan yansıması canlı geri sayımı sıfırladı — canlı yansıma bu tabanla hiç ateşlemeyebilir"
    assert hr._state["bg_reflect_by_regime"] == {"trend_down": n}
    # Arka plan turu yine GÖRÜNÜR bir yansımadır: sayaç ve son sonuç panoya düşer.
    assert hr._state["reflections"] == 1 and hr._state["last_result"] == "rejected_by_backtest"
    # Bekçinin okuyucusu (TSK-204 (A) ayağı) canlı ilerlemeyi korunmuş görür.
    kapi = hr.yansima_kapisi(dict(hr._state))
    assert kapi["last_reflect_at"] == TABAN and kapi["trades_since_last_reflection"] == every - 2


# =================================================================================================
# (2) CANLI YANSIMA tabanı TAŞIR (davranış birebir)
# =================================================================================================
def test_2_canli_yansima_tabani_TASIR(dongu):
    kos, cagrilar = dongu
    every = _every()
    _kur(every)                                       # canlı vade doldu (sayı + 60 gün takvim)
    n = _defter_n()
    kos()
    assert cagrilar == [{"rejim": CANLI, "arka_plan": False, "defter": n}], cagrilar
    assert hr._state["last_reflect_at"] == n
    assert "bg_reflect_by_regime" not in hr._state, "canlı yansıma arka plan tabanına dokundu"
    assert hr.yansima_kapisi(dict(hr._state))["trades_since_last_reflection"] == 0


# =================================================================================================
# (3) ELLE YANSIMA (`reflect_now`) tabanı TAŞIR (davranış birebir)
# =================================================================================================
def test_3_elle_yansima_tabani_TASIR(dongu, monkeypatch):
    _kos, cagrilar = dongu
    every = _every()
    _kur(every - 2)
    hr._state["last_reflect_at"] = TABAN
    n = _defter_n()
    monkeypatch.setattr(hr, "status", lambda: {"horizon": {"ready": False, "trades": every - 2,
                                                           "trades_needed": every, "span_days": 30,
                                                           "min_days": 30}})
    monkeypatch.setattr(hr, "threading", types.SimpleNamespace(Thread=_EsZamanliIplik))
    out = hr.reflect_now()
    assert out["status"] == "started", out
    assert cagrilar == [{"rejim": "auto", "arka_plan": False, "defter": n}], cagrilar
    assert hr._state["last_reflect_at"] == n, \
        "elle yansıma geri sayımı taşımadı — döngü aynı işlemler üzerinde hemen yeniden yansırdı"


# =================================================================================================
# (4) SENARYO — araya giren arka plan yansımalarına rağmen canlı vade dolar (livelock çözüldü)
# =================================================================================================
def test_4_senaryo_arka_plan_araya_girse_de_canli_vade_DOLAR_ve_yansima_ATESLER(dongu):
    """Tur 1: canlı every-2 → arka plan (trend_down). Kapanış +1. Tur 2: canlı every-1 → arka plan (high_vol).
    Kapanış +1. Tur 3: canlı every → CANLI yansıma. Eski kodda her arka plan turu sayacı sıfırlıyordu: tur 3'te
    canlı sayaç 1 kalır, arka plan adayı da kalmaz → hiçbir yansıma ateşlemez (livelock)."""
    kos, cagrilar = dongu
    every = _every()
    _kur(every - 2)
    goruldu: list[dict] = []

    def _tur_sonu(sonraki_i):
        def _adim():
            goruldu.append({"last_reflect_at": hr._state["last_reflect_at"],
                            "bg": dict(hr._state.get("bg_reflect_by_regime") or {})})
            _kapanis_ekle(sonraki_i)
            kapi = hr.yansima_kapisi(dict(hr._state))
            goruldu[-1].update(vade_doldu=kapi["vade_doldu"], ilerleme=kapi["trades_since_last_reflection"])
        return _adim

    n1 = _defter_n()
    kos([_tur_sonu(every - 2), _tur_sonu(every - 1)])
    n3 = _defter_n()
    assert n3 == TABAN + every

    assert [(c["rejim"], c["arka_plan"]) for c in cagrilar] == \
        [("trend_down", True), ("high_vol", True), (CANLI, False)], cagrilar
    # Arka plan turlarından sonra canlı taban YERİNDE; her arka plan turu kendi rejim tabanını taşıdı.
    assert goruldu[0]["last_reflect_at"] == TABAN and goruldu[0]["bg"] == {"trend_down": n1}
    assert goruldu[1]["last_reflect_at"] == TABAN and goruldu[1]["bg"] == {"trend_down": n1, "high_vol": n1 + 1}
    # Canlı sayaç arka plan turlarına rağmen ilerledi; tur 3 öncesi bekçinin okuyucusu vadeyi GÖRÜYOR ((A) kör değil).
    assert [g["ilerleme"] for g in goruldu] == [every - 1, every]
    assert [g["vade_doldu"] for g in goruldu] == [False, True]
    assert hr._yansima_vadesi(store.read_jsonl("trades.jsonl"), TABAN, every, CANLI) is True
    # Canlı yansıma tabanı taşıdı (davranış birebir).
    assert hr._state["last_reflect_at"] == n3


# =================================================================================================
# (5) YAPI — `arka_plan` ZORUNLU ve ADIYLA; her çağrı yerinin beyanı yansımanın `background` bayrağıyla AYNI
# =================================================================================================
def test_5_record_arka_plan_parametresi_ZORUNLU_ve_cagri_yerleri_ADIYLA():
    p = inspect.signature(hr._record).parameters.get("arka_plan")
    assert p is not None, "_record `arka_plan` parametresi taşımıyor"
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is inspect.Parameter.empty, \
        "`arka_plan` yalnız-adla ve varsayılansız olmalı — beyansız çağrı canlı tabanı sessizce taşırdı"
    agac = ast.parse(inspect.getsource(hr))
    cagrilar = [c for c in ast.walk(agac)
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "_record"]
    assert len(cagrilar) == 3, f"_record çağrı yeri sayısı değişti ({len(cagrilar)}) — beyanları yeniden denetle"
    beyanlar = []
    for c in cagrilar:
        kw = {k.arg: k.value for k in c.keywords}
        assert isinstance(kw.get("arka_plan"), ast.Constant), ast.unparse(c)
        ic = c.args[0]
        assert isinstance(ic, ast.Call) and ast.unparse(ic.func) == "hermes.reflect_once", ast.unparse(c)
        bayrak = next((k.value.value for k in ic.keywords
                       if k.arg == "background" and isinstance(k.value, ast.Constant)), False)
        assert kw["arka_plan"].value is bayrak, \
            f"beyan yansımanın türüyle çelişiyor: {ast.unparse(c)}"
        beyanlar.append(kw["arka_plan"].value)
    assert sorted(beyanlar) == [False, False, True]     # canlı + elle taşır, arka plan taşımaz


# =================================================================================================
# (6) ÖLÇÜM (brief) — arka plan rejim tabanı kalıcı durum dosyasına YAZILIR
# =================================================================================================
def test_6_arka_plan_rejim_tabani_kalici_durum_dosyasina_YAZILIR(sandbox_state, monkeypatch):
    """`_persist` `_state`in tamamını `hermes_status.json`a döker; arka plan tabanı da diske iner. (Açılışta GERİ
    OKUNMASI ayrı bir sorudur — TSK-227 raporunda kaygı; bu çivi yalnız yazım yarısını ölçer.)"""
    monkeypatch.setattr(hr, "_state", {"reflections": 1, "last_reflect_at": TABAN,
                                       "bg_reflect_by_regime": {"trend_down": TABAN + 3}})
    monkeypatch.setattr(hr, "_brain", lambda: "deterministic")
    monkeypatch.setattr(hr, "_brain_availability", lambda: {})
    monkeypatch.setattr(hr, "_brain_chain", lambda: {})
    hr._persist()
    disk = store.read_json(hr.STATUS_FILE, {})
    assert disk.get("bg_reflect_by_regime") == {"trend_down": TABAN + 3}
    assert disk.get("last_reflect_at") == TABAN

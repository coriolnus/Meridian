"""test_bg_taban_geri_yukleme_v562.py — TSK-229: arka plan rejim tabanı (`bg_reflect_by_regime`) restart'ta kalıcı
durumdan GERİ YÜKLENİR.

BULGU (TSK-227 ölçümü, 2026-09-26): `hermes_runtime._persist` alanı `hermes_status.json`a yazıyordu ama açılışta hiçbir
yol onu geri okumuyordu. Diskte `{"trend_down": 21}` varken taze süreç (`_state` boş) AYNI kanıtla trend_down arka plan
yansımasını yeniden başlattı — `_bg_ready_regime`in "aynı kanıta ikinci kez yansıma yok" güvencesi restart'ta tutmuyordu.
Bedel: gereksiz LLM+arama turu (TSK-227 sonrası canlı taban `last_reflect_at` bundan etkilenmiyor).

KARAR (Rol-1, 2026-09-26): açılışta alan kalıcı durumdan geri yüklenir — `last_reflect_at`ı geri yükleyen yolun
(`_restored_baseline`) AYNI kaynağı (STATUS_FILE) ve deseniyle (süreç başına bir kez, `_run` başında). Sınır: her değer
`min(değer, len(defter))`; negatif / tam sayı olmayan / bilinmeyen tipte değer ELENİR, sessiz değil (uyarı olayı). Dosya
ya da alan yoksa bugünkü davranış.

ÇİVİLER bekleme döngüsünü (`_run`) GERÇEK `_persist` ile koşturur (yalnız beyin ölçümleri sahte): geri yüklemenin ilk
yazımdan ÖNCE olması da böylece ölçülür — sonra olsaydı ilk `_persist` disk alanını `_state`le ezer, geri yüklenecek bir
şey kalmazdı. "Taze süreç" = modül `_state`inin import anındaki başlangıç sözlüğü; elle kopyalanmaz, kaynaktan (AST)
okunur. Senaryo verisi ve adımlı durdurucu v560'tan gelir (tek kaynak).
"""
from __future__ import annotations

import ast
import datetime as dt
import inspect

import pytest

from meridian import health, hermes, store, watchdog
from meridian import hermes_runtime as hr
from tests.test_yansima_taban_v560 import (CANLI, TABAN, _AdimliDurdurucu, _birikmis, _canli, _defter_n, _every,
                                           _islem)

UYARI = "hermes_bg_taban_elendi"
_YOK = object()


def _ilk_state() -> dict:
    """Modül düzeyindeki `_state` başlangıç sözlüğü — taze bir sürecin import anında gördüğü hâl (kaynaktan okunur)."""
    for dugum in ast.parse(inspect.getsource(hr)).body:
        if isinstance(dugum, ast.AnnAssign) and isinstance(dugum.target, ast.Name) and dugum.target.id == "_state":
            return ast.literal_eval(dugum.value)
    raise AssertionError("hermes_runtime modül düzeyinde `_state` başlangıç sözlüğü bulunamadı")


def _kur(n_canli: int, bg=_YOK, *, dosya: bool = True) -> int:
    """Defter = birikmiş (18) + `n_canli` canlı kapanış; canlı rejim `CANLI`. Kalıcı durum: `last_reflect_at = TABAN`
    (+ verildiyse önceki sürecin `bg_reflect_by_regime`i). `dosya=False` → STATUS_FILE hiç yok. Defter uzunluğunu döner."""
    store.write_jsonl("trades.jsonl", _birikmis() + [_canli(i) for i in range(n_canli)])
    store.write_json("regime.json", {"regime": CANLI})
    if dosya:
        disk = {"last_reflect_at": TABAN}
        if bg is not _YOK:
            disk["bg_reflect_by_regime"] = bg
        store.write_json(hr.STATUS_FILE, disk)
    return _defter_n()


def _uyarilar() -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == UYARI]


@pytest.fixture
def taze_surec(sandbox_state, monkeypatch):
    """Yeni başlamış bir öğrenme süreci → `(kos, cagrilar)`.

    `_state` import-anı başlangıcındadır. Sahte olan yalnız DIŞ yüzeylerdir (yansımanın kendisi, sağlık bayrakları,
    öz-onarım eşitlemeleri, nabız, beyin/zincir ölçümleri); `_restored_baseline`, geri yükleme, `_persist` (gerçek
    disk yazımı), dal seçimi ve `_bg_ready_regime` GERÇEKTİR."""
    monkeypatch.setattr(hr, "_state", _ilk_state())
    monkeypatch.setattr(hr, "_thread", None)
    monkeypatch.setattr(hr, "_acilis_senkron_calisti", True)        # açılış senkronu alt süreç koşturur — konu değil
    monkeypatch.setattr(hr, "_brain", lambda: "deterministic")
    monkeypatch.setattr(hr, "_brain_availability", lambda: {})
    monkeypatch.setattr(hr, "_brain_chain", lambda: {})
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: {})
    monkeypatch.setattr(hermes, "config_ensure_integrations", lambda: {})
    monkeypatch.setattr(watchdog, "beat", lambda _ad: None)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(health, "stale", lambda *_a, **_k: False)
    monkeypatch.setattr(health, "learn_halted", lambda: False)
    monkeypatch.setenv("MERIDIAN_BG_REFLECT", "1")
    monkeypatch.setenv("MERIDIAN_WARMUP_SPRINTS", "0")               # ısınma dalı bu çivinin konusu değil
    cagrilar: list[dict] = []

    def _sahte_yansima(target_regime="auto", *, background=False, durdurma=None):
        # `durdurma`: TSK-248 imzası — döngü `_stop.is_set` yüklemini iletir; bu çivinin konusu değil (v588 ölçer).
        cagrilar.append({"rejim": target_regime, "arka_plan": background, "defter": _defter_n()})
        return {"status": "rejected_by_backtest", "hypothesis": {"variable": f"exit.trail_atr_mult@{target_regime}"}}

    monkeypatch.setattr(hermes, "reflect_once", _sahte_yansima)

    def kos(adimlar=()):
        monkeypatch.setattr(hr, "_stop", _AdimliDurdurucu(adimlar))
        hr._run(poll_seconds=1)
        # `_run` poll içindeki her istisnayı `last_result = "error: …"` olarak yutar — kurulum hatası yeşil görünmesin.
        assert not str(hr._state.get("last_result") or "").startswith("error"), hr._state.get("last_result")

    return kos, cagrilar


# =================================================================================================
# (1) RESTART — diskteki taban geri yüklenir; önceki sürecin yansıdığı kanıtla arka plan yansıması BAŞLAMAZ
# =================================================================================================
def test_1_restart_diskteki_taban_GERI_YUKLENIR_ayni_kanitla_arka_plan_yansimasi_BASLAMAZ(taze_surec):
    kos, cagrilar = taze_surec
    every = _every()
    n = TABAN + every - 2
    onceki = {"trend_down": n, "high_vol": n}         # önceki süreç iki rejime de bu defterle yansıdı
    assert _kur(every - 2, onceki) == n
    assert "bg_reflect_by_regime" not in hr._state    # taze süreç: import-anı başlangıcında alan yok
    kos()
    assert cagrilar == [], \
        f"taze süreç önceki sürecin zaten yansıdığı AYNI kanıtla arka plan yansıması başlattı: {cagrilar}"
    assert hr._state["bg_reflect_by_regime"] == onceki
    assert hr._state["_warm_skip"] == "disabled"      # arka plan dalı seçilmedi (ısınma kapalı → son dal)
    assert hr._state["last_reflect_at"] == TABAN      # canlı taban geri yüklemesi birebir (`_restored_baseline`)
    # Geri yükleme ilk `_persist`ten ÖNCE: taban diskte korunur (sonra olsaydı ilk yazım alanı silerdi).
    assert store.read_json(hr.STATUS_FILE, {}).get("bg_reflect_by_regime") == onceki


# =================================================================================================
# (2) REJİM BAŞINA — yalnız yansınmış rejim durur; yansınmamış rejimin kanıtı yine işlenir
# =================================================================================================
def test_2_geri_yukleme_REJIM_BASINA_yalniz_yansinmis_rejimi_durdurur(taze_surec):
    """Geri yükleme öncesi seçici trend_down'u (10 işlem > high_vol 8) YENİDEN seçiyordu. Şimdi trend_down tabanı n'de:
    yeni trend_down kanıtı yok → seçici yansınmamış high_vol'a geçer."""
    kos, cagrilar = taze_surec
    every = _every()
    n = _kur(every - 2, {"trend_down": TABAN + every - 2})
    kos()
    assert [(c["rejim"], c["arka_plan"]) for c in cagrilar] == [("high_vol", True)], cagrilar
    assert hr._state["bg_reflect_by_regime"] == {"trend_down": n, "high_vol": n}
    assert hr._state["last_reflect_at"] == TABAN


# =================================================================================================
# (3) KIRPMA — defterden büyük taban defter uzunluğuna kırpılır; rejim gelecekte bir tabana takılmaz
# =================================================================================================
def test_3_defterden_buyuk_taban_KIRPILIR_ve_rejim_yeni_kanitla_yeniden_secilir(taze_surec):
    """Defter kısalmış/yeniden tohumlanmışsa kalıcı taban defterin ötesini gösterir. Kırpılmasaydı `trades[999:]` defter
    999'a ulaşana dek boş kalır, o rejim yeni kanıtı ne olursa olsun hiç seçilmezdi."""
    kos, cagrilar = taze_surec
    every = _every()
    n = _kur(every - 2, {"trend_down": 999, "high_vol": 10_000})
    assert hr._restored_bg_baselines() == {"trend_down": n, "high_vol": n}

    def _yeni_trend_down_kaniti():
        # Tur 1 sonu: `every` yeni trend_down kapanışı, 15 gün arayla (yayılım ≥ 30 günlük takvim tabanı).
        for k in range(every):
            store.append_jsonl("trades.jsonl", _islem("trend_down", str(dt.date(2026, 2, 10) + dt.timedelta(days=15 * k))))

    kos([_yeni_trend_down_kaniti])
    assert cagrilar == [{"rejim": "trend_down", "arka_plan": True, "defter": n + every}], \
        f"kırpılmamış taban rejimi geleceğe kilitledi — yeni kanıt işlenmedi: {cagrilar}"
    assert hr._state["bg_reflect_by_regime"] == {"trend_down": n + every, "high_vol": n}
    assert hr._state["last_reflect_at"] == TABAN      # canlı vade dolmadı (trend_up ufku every-2) — canlı tur yok


# =================================================================================================
# (4) ELEME — bozuk değer elenir (uyarıyla); elenen rejim tabansız sayılır, döngü düşmez
# =================================================================================================
def test_4a_bozuk_deger_ELENIR_gecerli_deger_kalir_ve_uyari_ADIYLA_duser(taze_surec):
    """Sayıya çevrilemeyen dizge, negatif, bool (JSON `true` Python'da int'tir), kesirli, null ve liste ELENİR; geçerli
    tam sayı kalır. Uyarı her eleneni rejim adı ve gerekçesiyle taşır (sessiz eleme yok)."""
    _kur(_every() - 2, {"trend_down": "bozuk", "high_vol": -3, "chop": True, "x_kesirli": 2.5,
                        "x_null": None, "x_liste": [1], "trend_up": 7})
    assert hr._restored_bg_baselines() == {"trend_up": 7}
    uyari = _uyarilar()
    assert len(uyari) == 1, uyari
    elenen = uyari[0].get("elenen") or {}
    assert sorted(elenen) == ["chop", "high_vol", "trend_down", "x_kesirli", "x_liste", "x_null"], elenen
    assert all(isinstance(v, str) and v for v in elenen.values()), elenen    # her elemenin gerekçesi var


def test_4b_alan_sozluk_degilse_ELENIR_ve_uyari_duser(taze_surec):
    _kur(_every() - 2, [["trend_down", 21]])
    assert hr._restored_bg_baselines() == {}
    assert len(_uyarilar()) == 1


def test_4c_bozuk_deger_dongude_ELENIR_rejim_tabansiz_sayilir_dongu_DUSMEZ(taze_surec):
    """Elenmeseydi: sayıya çevrilemeyen değer `_bg_ready_regime`in `int()`inde her poll'u istisnaya düşürürdü (arka plan
    VE ısınma dalı birlikte ölür); negatif taban `trades[-k:]` ile defterin SONUNU okurdu (yanlış kanıt penceresi).
    Elenen rejim tabansız = bugünkü (geri yüklemesiz) davranış: trend_down'un birikmiş kanıtı işlenir."""
    kos, cagrilar = taze_surec
    every = _every()
    n = _kur(every - 2, {"trend_down": "bozuk", "high_vol": TABAN + every - 2})
    kos()
    assert [(c["rejim"], c["arka_plan"]) for c in cagrilar] == [("trend_down", True)], cagrilar
    assert hr._state["bg_reflect_by_regime"] == {"trend_down": n, "high_vol": n}
    assert len(_uyarilar()) == 1


# =================================================================================================
# (5) SÜREÇ BAŞINA BİR KEZ — aynı süreçte stop→start süreç-içi (daha taze) tabanı diskteki bayat değerle EZMEZ
# =================================================================================================
def test_5_ayni_surecte_yeniden_baslatma_surec_ici_tabani_EZMEZ(taze_surec):
    kos, cagrilar = taze_surec
    every = _every()
    n = _kur(every - 2, {"trend_down": 3, "high_vol": 3})     # disk bayat (örn. başka sürecin yazımı)
    hr._state["bg_reflect_by_regime"] = {"trend_down": n, "high_vol": n}
    kos()
    assert cagrilar == [], f"süreç-içi taban diskteki bayat değerle ezildi: {cagrilar}"
    assert hr._state["bg_reflect_by_regime"] == {"trend_down": n, "high_vol": n}


# =================================================================================================
# (6) DOSYA YOK / ALAN YOK — bugünkü davranış birebir
# =================================================================================================
@pytest.mark.parametrize("hal", ["dosya_yok", "alan_yok"])
def test_6_dosya_ya_da_alan_yoksa_BUGUNKU_davranis(taze_surec, hal):
    kos, cagrilar = taze_surec
    every = _every()
    n = _kur(every - 2, dosya=(hal != "dosya_yok"))
    assert hr._restored_bg_baselines() == {}
    kos()
    # Geri yüklenecek taban yok → seçici birikmiş kanıtın en büyüğünü (trend_down 10 > high_vol 8) seçer — bugünkü hâl.
    assert [(c["rejim"], c["arka_plan"]) for c in cagrilar] == [("trend_down", True)], cagrilar
    assert hr._state["bg_reflect_by_regime"] == {"trend_down": n}
    assert _uyarilar() == []                          # yokluk bir bozukluk değildir — uyarı yok
    # `_restored_baseline` birebir: dosya yoksa taban = defter uzunluğu, varsa kalıcı değer.
    assert hr._state["last_reflect_at"] == (n if hal == "dosya_yok" else TABAN)

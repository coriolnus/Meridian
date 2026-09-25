"""test_seans_takvimi_v548.py — TSK-223: seans kapısı resmî TATİLİ ve ERKEN KAPANIŞI XNYS takviminden bilir.

SORUN (Rol-1 ölçümü, 2026-09-25): `barclock.is_market_open` yalnız saat + DST + hafta sonu biliyordu;
resmî tatil ve erken kapanış (13:00 ET) bilmiyordu, `is_entry_window` aynı sınırı taşıyordu. İki canlı
sonuç:
  1. ÇIKIŞ KAPISI (TSK-205: `loop._mirror_exit_sync` + `loop.mirror_exit_acilis_turu`): erken kapanış
     günü akşam döngüsü ~13:16 ET'de koşar, kapı "açık" sanır → koruma bacakları iptal + kapatma seans
     DIŞINDA kuyruklanır → pozisyon ertesi açılışa dek korumasız. Tatil sabahı açılış turu da "açık" sanır.
  2. GİRİŞ PENCERESİ (`loop.mirror_submit_armed` pencere yasası, EXE-2026-009 + K2): erken kapanış günü
     13:16 ET'de `is_entry_window()` True görür (16:00 varsayar) → giriş emri kapanıştan SONRA gider, gece
     dinlenip ertesi AÇILIŞTA dolar — pencere yasasının önlemek için var olduğu şey.

KARAR (Rol-1, 2026-09-25): kaynak XNYS takvimi (`pandas_market_calendars`), Alpaca `/v2/clock` DEĞİL —
depo seans gerçeğini zaten bu takvimden okuyor; ağdan ikinci bir saat kaynağı "aynı zaman iki kaynak"
sınıfıdır. Takvim okunamazsa kapı KAPALI döner (fail-closed) ve süreç başına BİR uyarı basılır —
uyarıyı barclock DEĞİL zamanlayıcı poll'ü basar (tur 2: saf yaprak sözleşmesi, v549).

TAKVİM ÖLÇÜMÜ (Rol-1, 2026-09-25, yerel `.venv` ve A1 `/opt/meridian/.venv` — ikisi de
`pandas_market_calendars 5.4.0`): hafta içi seanssız günler ve erken kapanışlar aşağıdaki
`HAFTA_ICI_TATILLER` / `ERKEN_KAPANISLAR` listeleridir (kaynaktan AYNEN).

ÇİVİLER:
  T  tatil günü → `is_market_open` ve `is_entry_window` kapalı (ölçülen listenin tamamı)
  E  erken kapanış → 12:59 ET açık, 13:00 ET kapalı; 13:16 ET (akşam döngüsü) pencere kapalı
  N  normal gün sınırları (9:29/9:30/15:59/16:00; pencere 9:44/9:45) — regresyon
  D  DST (kış günü 14:30Z açık, 14:29Z kapalı)
  F  takvim okunamaz → kapalı (fail-closed, barclock SAF: `seans_durumu` arızayı dışarı verir);
     uyarı TAM bir kez ve TEK noktadan (zamanlayıcı poll'ü); arıza önbelleğe ALINMAZ
  G  entegrasyon: tatilde çıkış kapısı kapatmayı çağırmaz; erken kapanış 13:20 ET'de giriş gönderimi
     ertelenir; tatilde intraday `skipped["session"]` artar (her birinin POZİTİF kontrolü yanında)
  K  tek kaynak: barsarchive seans aralığını barclock'un yardımcısından alır; `schedule()` tek yerde
     + barclock SIFIR meridian import'u taşır (saf yaprak — mimari sözleşme v549)

Saat ya açık `at` argümanıyla ya da `barclock.set_clock` enjeksiyonuyla verilir — hiçbir test duvar
saatine bağlı değildir. `set_clock` ve seans önbelleği modül-globaldir: autouse fikstür sıfırlar.
"""
from __future__ import annotations

import ast
import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from meridian import barclock, barsarchive, config, intraday_cycle as ic, loop, store

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")
REPO = Path(__file__).resolve().parents[1]

# Rol-1 takvim ölçümü (2026-09-25, pandas_market_calendars 5.4.0 — yerel ve A1 aynı sürüm).
HAFTA_ICI_TATILLER = ("2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18",
                      "2027-02-15", "2027-03-26", "2027-05-31", "2027-06-18", "2027-07-05",
                      "2027-09-06", "2027-11-25", "2027-12-24")
ERKEN_KAPANISLAR = ("2026-11-27", "2026-12-24", "2027-11-26")     # 13:00 ET kapanış
NORMAL_GUN = "2026-09-25"                                          # Cuma, tam seans (EDT)
EV_TAKVIM_YOK = "session_gate_calendar_unavailable"


def _et(gun: str, saat: int, dakika: int, saniye: int = 0) -> dt.datetime:
    """NY duvar saatinden UTC an — testin kendi dönüşümü (zoneinfo), barclock'a dayanmaz."""
    y, a, g = (int(x) for x in gun.split("-"))
    return dt.datetime(y, a, g, saat, dakika, saniye, tzinfo=NY).astimezone(UTC)


@pytest.fixture(autouse=True)
def _temiz():
    """Seans önbelleği ve enjekte saat MODÜL GLOBALİDİR — bir testin taktığı sahte takvim/saat
    sonrakine sızarsa test kendi kurmadığı dünyayla 'geçiyor' görünür (v170/v175 dersi). Önbellek
    barsarchive adıyla temizlenir: K3 onun barclock'unkiyle AYNI nesne olduğunu ayrıca çiviler."""
    barsarchive._SEANS_CACHE.clear()
    ic._CONSUMER = None
    yield
    barclock.reset_clock()
    barsarchive._SEANS_CACHE.clear()
    ic._CONSUMER = None


# =================================================================================================
# T · TATİL
# =================================================================================================
@pytest.mark.parametrize("gun", ["2026-12-25", "2026-11-26"], ids=["noel", "sukran"])
def test_T1_tatil_sabahi_seans_ve_pencere_kapali(gun):
    """KIRMIZI-ÖNCE: tatil kontrolü kalkarsa 10:00 ET 'açık' görünür (eski davranış)."""
    an = _et(gun, 10, 0)
    assert an.astimezone(NY).weekday() < 5, "ön koşul: hafta içi olmalı (hafta sonu kısa devresi değil)"
    assert barclock.is_market_open(an) is False, f"{gun} tatil — seans açık sanıldı"
    assert barclock.is_entry_window(an) is False, f"{gun} tatil — giriş penceresi açık sanıldı"


@pytest.mark.parametrize("gun", HAFTA_ICI_TATILLER)
def test_T2_olculen_tum_hafta_ici_tatiller_kapali(gun):
    """Rol-1'in ölçtüğü listenin TAMAMI: hafta içi, gün ortasında kapalı."""
    for saat, dakika in ((9, 30), (10, 0), (12, 0), (15, 59)):
        an = _et(gun, saat, dakika)
        assert an.astimezone(NY).weekday() < 5, f"ön koşul: {gun} hafta içi değil"
        assert barclock.is_market_open(an) is False, f"{gun} {saat}:{dakika:02d} ET açık sanıldı"
        assert barclock.is_entry_window(an) is False


# =================================================================================================
# E · ERKEN KAPANIŞ (13:00 ET)
# =================================================================================================
@pytest.mark.parametrize("gun", ERKEN_KAPANISLAR)
def test_E1_erken_kapanis_1259_acik_1300_kapali(gun):
    """KIRMIZI-ÖNCE: kapanış sabit 16:00 kalırsa 13:00 ET 'açık' görünür."""
    assert barclock.is_market_open(_et(gun, 9, 30)) is True, "erken kapanış günü sabah açılmadı"
    assert barclock.is_market_open(_et(gun, 12, 59)) is True
    assert barclock.is_market_open(_et(gun, 12, 59, 59)) is True
    assert barclock.is_market_open(_et(gun, 13, 0)) is False, f"{gun} 13:00 ET kapanış bilinmiyor"
    assert barclock.is_market_open(_et(gun, 15, 0)) is False


@pytest.mark.parametrize("gun", ERKEN_KAPANISLAR)
def test_E2_erken_kapanis_aksam_dongusu_1316_pencere_kapali(gun):
    """AKŞAM DÖNGÜSÜ VAKASI: 13:16 ET'de pencere 'açık' görünürse giriş emri kapanıştan SONRA gider,
    gece dinlenip ertesi açılışta dolar. POZİTİF kontrol: aynı gün sabah pencere AÇIK."""
    assert barclock.is_entry_window(_et(gun, 11, 0)) is True, "erken kapanış sabahı pencere açılmadı"
    assert barclock.is_entry_window(_et(gun, 13, 16)) is False, f"{gun} 13:16 ET pencere açık sanıldı"
    assert barclock.is_market_open(_et(gun, 13, 16)) is False


# =================================================================================================
# N · NORMAL GÜN — REGRESYON
# =================================================================================================
def test_N1_normal_gun_seans_sinirlari():
    assert barclock.is_market_open(_et(NORMAL_GUN, 9, 29)) is False
    assert barclock.is_market_open(_et(NORMAL_GUN, 9, 29, 59)) is False
    assert barclock.is_market_open(_et(NORMAL_GUN, 9, 30)) is True
    assert barclock.is_market_open(_et(NORMAL_GUN, 15, 59)) is True
    assert barclock.is_market_open(_et(NORMAL_GUN, 15, 59, 59)) is True
    assert barclock.is_market_open(_et(NORMAL_GUN, 16, 0)) is False


def test_N2_normal_gun_giris_penceresi_sinirlari():
    """`ENTRY_WINDOW_ET_MIN` (9:45 ET) DEĞİŞMEDİ; pencere seansın ALT kümesidir."""
    assert barclock.ENTRY_WINDOW_ET_MIN == 9 * 60 + 45
    assert barclock.pencere_rejimi() == "1345"
    assert barclock.is_entry_window(_et(NORMAL_GUN, 9, 30)) is False
    assert barclock.is_entry_window(_et(NORMAL_GUN, 9, 44)) is False
    assert barclock.is_entry_window(_et(NORMAL_GUN, 9, 45)) is True
    assert barclock.is_entry_window(_et(NORMAL_GUN, 15, 59)) is True
    assert barclock.is_entry_window(_et(NORMAL_GUN, 16, 0)) is False


def test_N3_tzsiz_an_UTC_sayilir():
    assert barclock.is_market_open(dt.datetime(2026, 9, 25, 14, 0)) is True       # 10:00 ET
    assert barclock.is_market_open(dt.datetime(2026, 12, 25, 15, 0)) is False     # Noel 10:00 ET
    assert barclock.is_entry_window(dt.datetime(2026, 9, 25, 14, 0)) is True


def test_N4_enjekte_saatle_argumansiz_cagri():
    """`at` verilmezse TEK saat `barclock.now()` — tatil bilgisi o yolda da geçerli."""
    barclock.set_clock(lambda: _et("2026-11-26", 10, 0))
    assert barclock.is_market_open() is False and barclock.is_entry_window() is False
    barclock.set_clock(lambda: _et(NORMAL_GUN, 10, 0))
    assert barclock.is_market_open() is True and barclock.is_entry_window() is True


# =================================================================================================
# D · DST
# =================================================================================================
def test_D1_kis_gunu_sinirlari_UTC():
    """2026-12-01 Salı (EST, UTC-5): açılış 14:30Z, kapanış 21:00Z."""
    kis = dt.datetime(2026, 12, 1, 14, 30, tzinfo=UTC)
    assert barclock.is_market_open(kis) is True
    assert barclock.is_market_open(kis - dt.timedelta(minutes=1)) is False           # 14:29Z
    assert barclock.is_market_open(dt.datetime(2026, 12, 1, 20, 59, tzinfo=UTC)) is True
    assert barclock.is_market_open(dt.datetime(2026, 12, 1, 21, 0, tzinfo=UTC)) is False
    # yaz (EDT) karşılığı: 13:30Z açılış
    assert barclock.is_market_open(dt.datetime(2026, 9, 25, 13, 30, tzinfo=UTC)) is True
    assert barclock.is_market_open(dt.datetime(2026, 9, 25, 13, 29, tzinfo=UTC)) is False


# =================================================================================================
# F · TAKVİM OKUNAMAZ → FAIL-CLOSED (SAF) + TEK UYARI (ZAMANLAYICI POLL'Ü) + ARIZA ÖNBELLEĞE ALINMAZ
# -------------------------------------------------------------------------------------------------
# TUR 2 (2026-09-25): barclock "saf yapraklar birbirinden bağımsız" import-linter sözleşmesinin
# üyesidir ve SIFIR meridian import'u taşır (v549 + K4). Arıza SAF biçimde dışarı verilir
# (`barclock.seans_durumu(at) -> (acik, takvim_hatasi)`); `session_gate_calendar_unavailable` uyarısını
# TEK çağıran nokta basar: zamanlayıcı poll'ü (`scheduler._seans_kapisi_takvim_denetimi`, her poll
# `loop.mirror_exit_acilis_turu`nun yanında). Bayrak uyarıyı basan modülde yaşar.
# =================================================================================================
class _PatlakSchedule:
    """`get_calendar` döner ama `schedule()` patlar — içe aktarma başarılı, sorgu başarısız dünya."""

    class _Takvim:
        @staticmethod
        def schedule(**_k):
            raise RuntimeError("takvim sorgusu patladı")

    @classmethod
    def get_calendar(cls, _ad):
        return cls._Takvim()


def _uyari_yakala(monkeypatch) -> list:
    import meridian.obs as obs
    from meridian import scheduler
    gorulen: list = []
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: gorulen.append((ev, kw)))
    # Bayrak SÜREÇ globalidir ve geri sıfırlanmaz (tasarım): başka bir test yakmışsa "bir kez basar"
    # iddiası kendiliğinden yeşile ya da kırmızıya döner. monkeypatch sonunda eski değeri geri koyar.
    monkeypatch.setattr(scheduler, "_SEANS_KAPISI_TAKVIM_UYARILDI", False)
    return gorulen


def _takvim_uyarilari(gorulen: list) -> list:
    return [kw for ev, kw in gorulen if ev == EV_TAKVIM_YOK]


def test_F1_takvim_ice_aktarilamazsa_kapi_kapali_saf_ve_poll_uyarisi_TAM_bir_kez(monkeypatch):
    """KIRMIZI-ÖNCE: arızada True dönülürse kapı assert'leri düşer (çıplak pencere açılır); barclock
    kendisi olay basarsa `barclock_uyarilari == []` düşer (saf yaprak sözleşmesi); poll noktasında
    bayrak kalkıp koşulsuz uyarılırsa uyarı sayısı 1'i aşar (300 sn poll → 288 satır/gün)."""
    from meridian import scheduler
    gorulen = _uyari_yakala(monkeypatch)
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", None)      # ImportError üretir
    acik_an = _et(NORMAL_GUN, 10, 0)                                         # takvim olsa AÇIK
    for _ in range(6):
        assert barclock.is_market_open(acik_an) is False, "takvim yokken kapı AÇIK döndü"
        assert barclock.is_entry_window(acik_an) is False
    acik, hata = barclock.seans_durumu(acik_an)
    assert acik is False and "ModuleNotFoundError" in str(hata), (acik, hata)
    assert gorulen == [], f"barclock SAF değil — olay bastı: {gorulen}"
    barclock.set_clock(lambda: acik_an)
    for _ in range(5):
        assert "ModuleNotFoundError" in str(scheduler._seans_kapisi_takvim_denetimi())
    kayit = _takvim_uyarilari(gorulen)
    assert len(kayit) == 1, f"tek-seferlik uyarı sözleşmesi kırıldı: {[e for e, _ in gorulen]}"
    assert "ModuleNotFoundError" in str(kayit[0].get("error")), "arıza sınıfı olaya geçmedi"
    assert kayit[0].get("gun") == NORMAL_GUN and kayit[0].get("takvim") == "XNYS"


def test_F2_schedule_istisnasi_da_kapi_kapali_tek_uyari(monkeypatch):
    from meridian import scheduler
    gorulen = _uyari_yakala(monkeypatch)
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", _PatlakSchedule)
    acik_an = _et(NORMAL_GUN, 10, 0)
    for _ in range(4):
        assert barclock.is_market_open(acik_an) is False
    assert "RuntimeError" in str(barclock.seans_durumu(acik_an)[1])
    barclock.set_clock(lambda: acik_an)
    for _ in range(4):
        scheduler._seans_kapisi_takvim_denetimi()
    kayit = _takvim_uyarilari(gorulen)
    assert len(kayit) == 1, [e for e, _ in gorulen]
    assert "RuntimeError" in str(kayit[0].get("error"))


def test_F3_takvim_donunce_ayni_surecte_dogru_sonuc(monkeypatch):
    """ARIZA ÖNBELLEĞE ALINMAZ: takvim geri gelince aynı süreçte kapı düzelir. KIRMIZI-ÖNCE: arıza
    önbelleğe alınırsa son assert'ler düşer (o gün sonsuza dek 'kapalı' kalırdı)."""
    import pandas_market_calendars as gercek
    from meridian import scheduler
    _uyari_yakala(monkeypatch)
    acik_an = _et(NORMAL_GUN, 10, 0)
    barclock.set_clock(lambda: acik_an)
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", None)
    assert barclock.is_market_open(acik_an) is False
    assert scheduler._seans_kapisi_takvim_denetimi() is not None
    assert NORMAL_GUN not in barsarchive._SEANS_CACHE, "ARIZA önbelleğe alındı"
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", gercek)
    assert barclock.seans_durumu(acik_an) == (True, None), "takvim döndü ama kapı düzelmedi"
    assert barclock.is_market_open(acik_an) is True
    assert barclock.is_entry_window(acik_an) is True
    assert scheduler._seans_kapisi_takvim_denetimi() is None, "poll noktası arızayı hâlâ görüyor"
    assert NORMAL_GUN in barsarchive._SEANS_CACHE, "başarı önbelleğe alınmadı"


def test_F4_hafta_sonu_takvim_sorulmadan_kapali_ve_uyari_yok(monkeypatch):
    """Hafta sonu kısa devresi: takvim hiç sorulmaz — arızada bile hata dönmez, poll uyarı basmaz
    (kapı zaten kapalı; arıza ilk hafta içi poll'ünde görünür)."""
    from meridian import scheduler
    gorulen = _uyari_yakala(monkeypatch)
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", None)
    cumartesi = _et("2026-09-26", 10, 0)
    assert barclock.is_market_open(cumartesi) is False
    assert barclock.seans_durumu(cumartesi) == (False, None)
    barclock.set_clock(lambda: cumartesi)
    assert scheduler._seans_kapisi_takvim_denetimi() is None
    assert gorulen == []


def test_F5_onbellek_yalniz_basariya_ve_tavanli(monkeypatch):
    """Barsarchive sözleşmesi aynen: başarı önbelleğe girer, arıza girmez, önbellek tavanlıdır."""
    class _Sahte:
        class _Takvim:
            @staticmethod
            def schedule(start_date, end_date):
                ac = pd.Timestamp(f"{start_date} 14:30", tz="UTC")
                return pd.DataFrame({"market_open": [ac],
                                     "market_close": [ac + pd.Timedelta(hours=6, minutes=30)]})

        @classmethod
        def get_calendar(cls, _ad):
            return cls._Takvim()

    monkeypatch.setitem(sys.modules, "pandas_market_calendars", _Sahte)
    gunler = [(dt.date(2031, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(55)]
    for g in gunler:
        assert barsarchive._seans_araligi(g)[0] == "ok"
    assert len(barsarchive._SEANS_CACHE) <= barclock.SEANS_CACHE_MAX, "önbellek tavanı yok"
    assert gunler[-1] in barsarchive._SEANS_CACHE and gunler[0] not in barsarchive._SEANS_CACHE


class _Dur(RuntimeError):
    """Poll akışının KONTROLLÜ kesildiği nokta (v545 E2 deseni): açılış turundan sonraki bar yüklemesi."""


def test_F6_zamanlayici_pollu_takvim_arizasini_surec_basina_TEK_uyariyla_anlatir(sandbox_state,
                                                                                   monkeypatch):
    """UYARININ TEK NOKTASI ZAMANLAYICI POLL'ÜDÜR: `advance_once` her poll'de seans takvimini sorar;
    arıza süreç başına BİR `session_gate_calendar_unavailable` ile anlatılır. KIRMIZI-ÖNCE: poll'deki
    uyarı noktası kaldırılırsa uyarı listesi BOŞ kalır; bayrak her poll'de sıfırlanırsa 3 poll 3
    uyarı basar. Kurulum v545 `_zamanlayici_kur` ile aynı: akış bar yüklemesinde kesilir."""
    from meridian import dataset, scheduler, watchdog
    gorulen = _uyari_yakala(monkeypatch)
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-09-24")
    monkeypatch.setattr(scheduler.health, "halted", lambda: False)
    monkeypatch.setattr(scheduler, "_repair_once_per_session", lambda s: None)
    monkeypatch.setattr(scheduler, "_intraday_gap_check", lambda: None)
    monkeypatch.setattr(watchdog, "check_and_alarm", lambda *a, **k: None)
    monkeypatch.setattr(dataset, "load_live", lambda *a, **k: (_ for _ in ()).throw(_Dur()))
    scheduler._state.update(refetch_chase=None, last_refetch_session="2026-09-24",
                            refetch_attempts=0, refetch_sparse_attempts=0,
                            learn_session="2026-09-24", dolgu_session="2026-09-24")
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", None)
    barclock.set_clock(lambda: _et(NORMAL_GUN, 10, 0))
    for _ in range(3):
        with pytest.raises(_Dur):
            scheduler.advance_once()
    kayit = _takvim_uyarilari(gorulen)
    assert len(kayit) == 1, f"poll uyarı sözleşmesi kırıldı: {[e for e, _ in gorulen]}"
    assert "ModuleNotFoundError" in str(kayit[0].get("error"))


# =================================================================================================
# G · ENTEGRASYON — üç tüketici (her birinin pozitif kontrolü yanında)
# =================================================================================================
@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """v545 sahte broker deseninin DAR hâli: `alpaca_paper` + erişim sağlıklı; `close_engine_position`
    CASUSTUR (ölçülen büyüklük çağrının KENDİSİ — kapı onu çağırdı mı). Ağa çıkılmaz."""
    from meridian.adapters import alpaca
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    cagrilar: list = []

    def _casus(symbol, plan_id=None):
        cagrilar.append((symbol, plan_id))
        return {"ok": True, "closed_qty": 0, "naked": False, "cancelled": [], "detail": "casus"}

    monkeypatch.setattr(alpaca, "close_engine_position", _casus)
    return cagrilar


def _kuyruk(sym="DE"):
    return {sym: {"plan_id": f"P-2026-11-25-{sym}", "reason": "time_stop", "since": "2026-11-25",
                  "tries": 0, "naked": False}}


@pytest.mark.parametrize("an,cagri_beklenir", [
    (_et("2026-11-26", 10, 0), False),     # Şükran günü sabahı — TATİL
    (_et("2026-11-27", 13, 16), False),    # erken kapanış günü akşam döngüsü (13:00 ET kapandı)
    (_et("2026-11-27", 10, 0), True),      # POZİTİF kontrol: erken kapanış günü sabahı seans AÇIK
], ids=["tatil_sabahi", "erken_kapanis_aksam_1316", "erken_kapanis_sabahi_acik"])
def test_G1_cikis_kapisi_tatil_ve_erken_kapanista_kapatmayi_cagirmaz(ayna, an, cagri_beklenir):
    """KIRMIZI-ÖNCE: kapı tatil/erken kapanış bilmezse casus çağrılır — koruma bacakları seans DIŞINDA
    iptal edilir, kapatma kuyruklanır ve pozisyon açılışa dek korumasız kalır (TSK-205 sınıfı)."""
    barclock.set_clock(lambda: an)
    meta = {loop.MIRROR_EXIT_KEY: _kuyruk("DE")}
    out = loop._mirror_exit_sync(meta, "2026-11-25")
    if cagri_beklenir:
        assert ayna == [("DE", "P-2026-11-25-DE")], "seans açıkken kapatma denenmedi"
        assert out["ertelendi"] == []
    else:
        assert ayna == [], f"seans kapalıyken kapatma çağrıldı: {ayna}"
        assert "DE" in meta[loop.MIRROR_EXIT_KEY], "ertelenen çıkış kuyruktan düştü"
        assert out["ertelendi"] == ["DE"]


def test_G2_tatil_sabahi_acilis_turu_calismaz(ayna):
    """`mirror_exit_acilis_turu` her poll'de koşar: tatil sabahı 'açık' sanarsa kapatma seans dışında
    kuyruklanır. POZİTİF kontrol: ertesi (erken kapanış) sabahı tur çalışır ve kapatır."""
    store.write_json(loop.PORTFOLIO, {"positions": {}, loop.MIRROR_EXIT_KEY: _kuyruk("DE")})
    barclock.set_clock(lambda: _et("2026-11-26", 10, 0))
    out = loop.mirror_exit_acilis_turu()
    assert out["calisti"] is False and out["neden"] == "seans_kapali", out
    assert ayna == []
    barclock.set_clock(lambda: _et("2026-11-27", 9, 35))
    out2 = loop.mirror_exit_acilis_turu()
    assert out2["calisti"] is True and ayna == [("DE", "P-2026-11-25-DE")], out2


def _meta():
    return {"armed": [{"id": "P1", "ticker": "AAPL", "entry_trigger": 100.0}],
            "alpaca_submitted": [], "entry_law": {}, "peak_equity": 100_000.0}


@pytest.mark.parametrize("an,ertelenir", [
    (_et("2026-11-27", 13, 20), True),     # erken kapanış 13:20 ET — kapanıştan SONRA
    (_et("2026-11-26", 10, 0), True),      # tatil sabahı (pano/onay yolu)
    (_et("2026-11-27", 11, 0), False),     # POZİTİF kontrol: erken kapanış sabahı pencere AÇIK
], ids=["erken_kapanis_1320", "tatil_sabahi", "erken_kapanis_sabahi_acik"])
def test_G3_giris_gonderimi_pencere_disinda_ertelenir(sandbox_state, monkeypatch, an, ertelenir):
    """KIRMIZI-ÖNCE: pencere erken kapanışı bilmezse 13:20 ET'de gönderim kapıdan GEÇER (gece dinlenip
    ertesi açılışta dolar). Ağsız kanıt: pencere geçilirse anahtar-yok dalına ulaşılır."""
    from meridian.adapters import alpaca
    monkeypatch.setattr(loop.config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)
    barclock.set_clock(lambda: an)
    meta = _meta()
    out = loop.mirror_submit_armed(meta, an.astimezone(NY).date().isoformat(), eq_now=100_000.0,
                                   halted=False, pencere_muaf=False)
    if ertelenir:
        assert out.get("deferred") is True and out["submitted"] == 0, out
        assert len(meta["armed"]) == 1, "ertelenen plan düşürüldü"
    else:
        assert out.get("deferred") is None, out
        assert "anahtar" in out["detail"], "pencere kapısı geçilmedi"


@pytest.mark.parametrize("an,seans_atlanir", [
    (_et("2026-11-26", 10, 46, 30), True),     # tatil
    (_et("2026-11-27", 13, 30), True),         # erken kapanış sonrası
    (_et(NORMAL_GUN, 10, 46, 30), False),      # POZİTİF kontrol: normal gün seans açık
], ids=["tatil", "erken_kapanis_sonrasi", "normal_gun"])
def test_G4_intraday_olay_tatilde_seans_sayacina_duser(sandbox_state, monkeypatch, an, seans_atlanir):
    barclock.set_clock(lambda: an)
    store.write_json("portfolio.json", {"positions": {"AAPL": {}}, "armed": []})
    if seans_atlanir:
        monkeypatch.setattr(ic.hotstate, "read_bars",
                            lambda tk, n: (_ for _ in ()).throw(AssertionError("seans dışı işlendi")))
    else:
        monkeypatch.setattr(ic.hotstate, "read_bars", lambda tk, n: None)
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    c = ic.consumer()
    assert c.last_error in (None, ""), c.last_error
    if seans_atlanir:
        assert c.skipped["session"] == 1, c.skipped
    else:
        assert c.skipped["session"] == 0 and c.skipped["no_bars"] == 1, c.skipped


# =================================================================================================
# K · TEK KAYNAK — seans aralığı barclock'un TEK yardımcısından
# =================================================================================================
def test_K1_barsarchive_ve_kapi_ayni_yardimcidan_okur(monkeypatch):
    """Yardımcı yamalanınca İKİ tüketici de değişir. KIRMIZI-ÖNCE: barsarchive kendi `schedule()`
    yoluna dönerse ilk assert düşer; kapı kendi takvim yolunu kurarsa ikinci assert düşer."""
    isaret = ("ok", dt.datetime(2030, 1, 2, 1, 0, tzinfo=UTC), dt.datetime(2030, 1, 2, 2, 0, tzinfo=UTC),
              None)
    sorulan: list = []

    def _sahte(gun):
        sorulan.append(str(gun))
        return isaret if str(gun) == "2030-01-01" else ("seans_disi", None, None, None)

    monkeypatch.setattr(barclock, "seans_araligi", _sahte)
    assert barsarchive._seans_araligi("2030-01-01") is isaret, "barsarchive yardımcıyı kullanmıyor"
    # normal gün 10:00 ET gerçek takvimde AÇIK; yardımcı 'seans_disi' derse kapı KAPALI olmalı
    assert barclock.is_market_open(_et(NORMAL_GUN, 10, 0)) is False, "kapı yardımcıyı kullanmıyor"
    assert NORMAL_GUN in sorulan


def _takvim_cagrilari(yol: Path) -> list:
    """Modüldeki takvim temasları (AST — yorum/docstring sayılmaz): `.schedule(`/`.get_calendar(`
    çağrıları ve `pandas_market_calendars` içe aktarımları, (tür, kapsayan fonksiyon) olarak."""
    agac = ast.parse(yol.read_text())
    bulgu: list = []

    def _gez(dugum, fn):
        for c in ast.iter_child_nodes(dugum):
            ad = c.name if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) \
                    and c.func.attr in ("schedule", "get_calendar", "valid_days"):
                bulgu.append((c.func.attr, ad))
            if isinstance(c, ast.Import) and any(a.name == "pandas_market_calendars" for a in c.names):
                bulgu.append(("import", ad))
            if isinstance(c, ast.ImportFrom) and c.module == "pandas_market_calendars":
                bulgu.append(("import", ad))
            _gez(c, ad)

    _gez(agac, None)
    return bulgu


def test_K2_takvim_sorgusu_barclockta_TEK_yerde():
    """İkinci bir `schedule()` yolu doğarsa öter: barsarchive takvime HİÇ dokunmaz, barclock'ta tek
    fonksiyon (`seans_araligi`) dokunur."""
    ba = _takvim_cagrilari(REPO / "meridian" / "barsarchive.py")
    assert ba == [], f"barsarchive kendi takvim yolunu taşıyor: {ba}"
    bc = _takvim_cagrilari(REPO / "meridian" / "barclock.py")
    assert {fn for _, fn in bc} == {"seans_araligi"}, f"barclock'ta takvim teması dağınık: {bc}"
    assert [t for t, _ in bc].count("schedule") == 1, bc


def test_K3_barsarchive_adlari_barclocka_bagli():
    """Uyumluluk adları testlerin beklediği biçimde yaşar ve barclock'a BAĞLIDIR (kopya değil)."""
    assert barsarchive._SEANS_CACHE is barclock._SEANS_CACHE, "önbellek iki kopya — ayrışır"
    assert barsarchive.GAP_CALENDAR == barclock.SEANS_TAKVIMI == "XNYS"
    assert barclock.SEANS_CACHE_MAX == 40


def test_K4_barclock_SIFIR_meridian_importu_tasir():
    """SAF YAPRAK (import-linter sözleşme 3): barclock'ta `meridian` ya da göreli (`from .`) import YOK
    — fonksiyon-içi tembel import DAHİL (statik analiz onu da kenar sayar; tur 1'in `from . import obs`u
    dağıtım kapısını böyle kırdı). v549 aynı gerçeği grafik düzeyinde ölçer; bu çivi kaynağı adıyla gösterir."""
    agac = ast.parse((REPO / "meridian" / "barclock.py").read_text())
    ihlal = []
    for d in ast.walk(agac):
        if isinstance(d, ast.ImportFrom) and (d.level > 0 or (d.module or "").split(".")[0] == "meridian"):
            ihlal.append(f"satır {d.lineno}: from {'.' * d.level}{d.module or ''} import …")
        if isinstance(d, ast.Import):
            ihlal += [f"satır {d.lineno}: import {a.name}" for a in d.names
                      if a.name.split(".")[0] == "meridian"]
    assert ihlal == [], f"barclock saf yaprak değil: {ihlal}"

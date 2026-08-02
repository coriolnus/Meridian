"""v175 — `takvim_yok`un SCHEDULER KANCASINDAKİ karşılığı (WP-D'nin ertelenen kalemi, 2026-08-02).

v170 `gap_scan`e ÜÇÜNCÜ bir hâl ekledi: XNYS takvimi okunamazsa beklenti üretilemez, dolayısıyla
eksiklik de ÖLÇÜLEMEZ ve ölçüm HÜKÜM VERMEZ (`durum="takvim_yok"`). Ölçüm SAF olduğu için kaydı
çağıran yapar — ama `scheduler._intraday_gap_check` bu hâli TANIMIYORDU. Üç sonucu vardı:

  1. Rapor ölçülmüş-sonuç dalına düşüyordu: `bosluklar` boş olduğu için sahte uyarı çıkmıyordu ama
     `_state["intraday_gap"]` ölçülmüş-ŞEKİLLİ bir kopya alıyordu (`bosluk_sayisi=0` vb.) — yani
     "ölçtüm, boşluk yok" ile "ölçemedim" state'te ayırt EDİLEMİYORDU.
  2. Arıza nedenini taşıyan `seans` bloğu (takvim adı + `hata`) kopyaya HİÇ girmiyordu; pano
     (`app.js:_gapRows`) bloğu korumalı okuyup yokluğunu normal saymak zorunda kalmıştı.
  3. Hâl olay defterinde TAMAMEN SESSİZDİ.

Bu küme üçünü de çiviler ve minimal-farkı ayrıca kilitler: `seans_disi`/`arsiv_yok` davranışı
DEĞİŞMEMİŞ olmalı. Uyarı SÜREÇ BAŞINA BİR KEZdir — kanca her poll'de (300 sn) koşar; koşulsuz
uyarı 288 satır/gün eder ve olay defterini boğardı (K1 seli dersi, kardeş `_CALENDAR_WARNED`).

KIRMIZI-ÖNCE: her testin docstring'i düzeltme geri alındığında hangi assert'in kırmızıya
döneceğini söyler. RAPORLAR EL YAPIMI DEĞİL: üç testin girdisi de GERÇEK `gap_scan` çıktısıdır —
uydurma bir sözlük, üreticinin şeması kaydığında testi yeşil bırakırdı.
"""
from __future__ import annotations

import datetime as dt
import sys

import pytest

UTC = dt.timezone.utc

TAM_GUN = "2025-11-26"      # GERÇEK bir XNYS tam günü (kapanış 21:00 UTC) — fikstür uydurmaz


@pytest.fixture(autouse=True)
def _seans_onbellegi_temiz():
    """`_SEANS_CACHE` MODÜL GLOBALİDİR — bir testin taktığı sahte/patlak takvim sonrakine sızarsa
    test kendi kurmadığı takvimle 'geçiyor' görünür (v133'ün, sonra v170'in aynı dersi)."""
    from meridian import barsarchive
    barsarchive._SEANS_CACHE.clear()
    yield
    barsarchive._SEANS_CACHE.clear()


@pytest.fixture(autouse=True)
def _kanca_defterleri_temiz():
    """`scheduler._state` de MODÜL GLOBALİDİR: kancanın bıraktığı kopya sonraki teste (ve aynı
    süreçteki başka dosyalara) sızar — v147 konvansiyonu gereği iki anahtar da temizlenir."""
    from meridian import scheduler
    for k in ("intraday_gap", "intraday_gap_seen"):
        scheduler._state.pop(k, None)
    yield
    for k in ("intraday_gap", "intraday_gap_seen"):
        scheduler._state.pop(k, None)


class _Patlak:
    """`pandas_market_calendars` yerine geçen patlak modül — takvim okunamayan dünyayı kurar."""

    @staticmethod
    def get_calendar(_ad):
        raise RuntimeError("takvim modülü yok")


def _takvim_yok_raporu(monkeypatch) -> dict:
    """GERÇEK `gap_scan`ten `takvim_yok` raporu üret (el yapımı sözlük DEĞİL)."""
    from meridian import barsarchive
    monkeypatch.setitem(sys.modules, "pandas_market_calendars", _Patlak)
    rapor = barsarchive.gap_scan(as_of=dt.datetime(2025, 11, 26, 19, 0, tzinfo=UTC),
                                 day=TAM_GUN, rows=[])
    assert rapor["durum"] == "takvim_yok", "fikstür üreticiyi yansıtmıyor"
    return rapor


def _seans_disi_raporu() -> dict:
    """GERÇEK `gap_scan`ten `seans_disi` raporu: takvim OKUNUR (gerçek XNYS), ama pencere gecenin
    içindedir — beklenti YOK, dolayısıyla eksiklik de yok."""
    from meridian import barsarchive
    rapor = barsarchive.gap_scan(as_of=dt.datetime(2025, 11, 27, 3, 0, tzinfo=UTC),
                                 day=TAM_GUN, rows=[])
    assert rapor["durum"] == "seans_disi", "fikstür üreticiyi yansıtmıyor"
    return rapor


def _kancayi_kur(monkeypatch, rapor: dict) -> list:
    """Kancayı raporla besle, `obs.warn`u listeye topla, tek-seferlik bayrağı sıfırla."""
    from meridian import barsarchive, scheduler
    import meridian.obs as obs
    gorulen: list = []
    monkeypatch.setattr(barsarchive, "gap_scan", lambda *a, **k: rapor)
    monkeypatch.setattr(scheduler.store, "write_json", lambda *a, **k: None)
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: gorulen.append((ev, kw)))
    # Bayrak SÜREÇ globalidir ve GERİ SIFIRLANMAZ (tasarım): başka bir test/dosya onu yakmış olursa
    # buradaki "bir kez basar" iddiası kendiliğinden yeşile döner. `monkeypatch` sonunda eski
    # değeri geri koyar, yani bu test kendi dışına da sızmaz.
    monkeypatch.setattr(scheduler, "_GAP_CALENDAR_WARNED", False)
    return gorulen


def test_takvim_yok_scheduler_SESSIZ_KALMAZ_ve_surec_basina_BIR_uyari(sandbox_state, monkeypatch):
    """SESSİZLİK KIRILDI, SEL AÇILMADI.

    KIRMIZI-ÖNCE: `gap_scan_calendar_unavailable` dalı kaldırılırsa uyarı listesi BOŞ kalır (ilk
    assert düşer); tek-seferlik bayrak kaldırılıp koşulsuz uyarılırsa ikinci çağrı da basar ve
    "tam bir uyarı" assert'i düşer (300 sn'lik poll'de 288 satır/gün)."""
    from meridian import scheduler
    rapor = _takvim_yok_raporu(monkeypatch)
    gorulen = _kancayi_kur(monkeypatch, rapor)

    scheduler._intraday_gap_check()
    scheduler._intraday_gap_check()

    adlar = [e for e, _ in gorulen]
    assert adlar == ["gap_scan_calendar_unavailable"], f"tek seferlik uyarı sözleşmesi kırıldı: {adlar}"
    assert "RuntimeError" in (gorulen[0][1].get("error") or ""), "arıza sınıfı olay defterine geçmedi"
    assert "intraday_gap_detected" not in adlar, "ölçülemeyen turda BOŞLUK HÜKMÜ basıldı"


def test_takvim_yok_state_HUKUMSUZ_ve_nedeni_tasir(sandbox_state, monkeypatch):
    """STATE 'ÖLÇEMEDİM' DER, 'BOŞLUK YOK' DEMEZ — ve NEDENİ yanında taşır.

    KIRMIZI-ÖNCE: erken-dönüş listesinden `takvim_yok` çıkarılırsa rapor ölçülmüş-sonuç dalına
    düşer, kopya `bosluk_sayisi` (=0) kazanır ve son assert düşer; `seans` bloğu taşınmazsa
    ortadaki iki assert düşer ve pano yine arıza nedenini göremez (app.js 4532'deki boşluk)."""
    from meridian import scheduler
    rapor = _takvim_yok_raporu(monkeypatch)
    _kancayi_kur(monkeypatch, rapor)

    scheduler._intraday_gap_check()
    st = scheduler._state["intraday_gap"]

    assert st["durum"] == "takvim_yok" and st["gun"] == TAM_GUN
    assert "seans" in st, "arıza nedeni state'e girmedi — pano teşhis edemez"
    assert "RuntimeError" in (st["seans"]["hata"] or "") and st["seans"]["takvim"] == "XNYS"
    assert "bosluk_sayisi" not in st, "ölçülemeyen tur ÖLÇÜLMÜŞ-ŞEKİLLİ kopya bıraktı"


def test_seans_disi_ve_arsiv_yok_davranisi_DEGISMEDI(sandbox_state, monkeypatch):
    """MİNİMAL FARK ÇİVİSİ: yeni hâl eklendi, eski iki hâl bit-bit AYNI kaldı.

    KIRMIZI-ÖNCE: `seans` bloğu (ya da uyarı) hâl ayrımı yapılmadan tüm erken-dönüşlere taşınırsa
    son iki assert düşer — pano `seans_disi` için de arıza nedeni varmış gibi okurdu."""
    from meridian import scheduler
    rapor = _seans_disi_raporu()
    gorulen = _kancayi_kur(monkeypatch, rapor)

    scheduler._intraday_gap_check()
    st = scheduler._state["intraday_gap"]

    assert gorulen == [], f"hükümsüz ama NORMAL hâl olay defterine yazdı: {gorulen}"
    assert set(st) == {"durum", "gun", "olculdu"}, "eski kopyanın anahtar kümesi değişti"
    assert st["durum"] == "seans_disi" and "seans" not in st

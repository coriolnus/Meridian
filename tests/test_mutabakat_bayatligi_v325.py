"""MUTABAKAT BAYATLIĞI ALARMLANIR — v325 (2026-08-26)

CANLI VAKA, ölçüldü ve bu çivi onu kapatıyor.

6 Ağustos'ta iç motor ile ayna aynı planı ayrı boyutladı (tasarım: kitap kâğıt
simülasyonu, ayna gerçek broker). Kitap BKNG'de 43 adet yazdı, brokere 22 gitmişti —
%95 fazla. Sapmayı yakalayacak tek mekanizma mutabakattır. O mekanizma 19 GÜN hüküm
üretmedi:

    11-21 Ağu   `reconcile_atlandi` ×9, hepsi sinif="noop", seviye **info**
                ("günlük tur reconcile'a varmadan döndü" — `bar already processed` dalı)
    22 Ağu      c726a19 benimseme yeteneğini getirdi, İÇİNDE HATAYLA
    22-24 Ağu   `reconcile_failed: TypeError: warn() takes 1 positional argument`
    25 Ağu      c001a11 onardı; mutabakat koştu ve 7 pozisyonda adedi benimsedi

19 gün boyunca kitap, olmayan hisselere karşı risk hesapladı. Kod kırık değildi —
ÖLÇÜM KOŞMUYORDU, ve koşmama hâli `info`/`noop` olarak İYİ HUYLU BİR HİÇLİK gibi
raporlanıyordu. Bu deponun kendi yasasının tersi: ölçülmemiş olan temiz görünemez.

SÖZLEŞME: mutabakatın atlandığı her gün, son BAŞARILI mutabakattan bu yana geçen
İŞLEM GÜNÜ sayısı ölçülür. Eşiği aşarsa `MECHANISM_STALE` alarmı basılır.

NEDEN TAKVİM GÜNÜ DEĞİL İŞLEM GÜNÜ — bu çivinin ayırt edici testi budur: cuma
mutabakat + pazartesi atlama = 3 TAKVİM günü ama 1 İŞLEM günü. Takvim günüyle yazılmış
bir eşik HER PAZARTESİ yanlış alarm verir, operatör alarmı susturur ve mekanizma
gerçekten bozulduğunda kimse bakmaz. `test_HAFTA_SONU_...` tam bu implementasyonu
reddeder.

NEDEN YENİ SAYAÇ YOK: son başarılı mutabakatın tarihi zaten `broker_reconcile.json`da
duruyor ve o dosya BAŞARISIZLIKTA HİÇ YAZILMIYOR (loop.py:2936 şerhi). İkinci bir
sayaç tutmak, ayrışabilecek ikinci bir gerçek üretirdi (`broker.py`de aynı gerekçeyle
`open_risk_dollars()` çıkarılmıştı — SATIR NUMARASI BİLEREK YOK: hedef bir yorum bloku,
çapa çürür ve codelaw bekçisi bu dosyanın İLK yazımında tam onu yakaladı).
"""
from __future__ import annotations

import pytest

from meridian import config, loop, obs, store

D_CUMA = "2026-08-21"       # Cuma
D_PZT = "2026-08-24"        # Pazartesi
# Döngünün gördüğü işlem takvimi (hafta sonu YOK — bars endeksi böyle gelir)
TAKVIM = ["2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24", "2026-08-25"]


@pytest.fixture(autouse=True)
def _temiz(monkeypatch, sandbox_state):
    """`sandbox_state` ZORUNLU — ilk yazımda `store.STATE_DIR`i elle saplamıştım ve depo
    bekçisi haklı olarak reddetti: "CANLI state'e YAZILDI". Çivi kendi kanıt defterini
    kirletemez; operatöre sunulan deftere düşen bir test artefaktı üretim arızası gibi okunur."""
    monkeypatch.setattr(config, "BROKER", "alpaca_paper", raising=False)
    loop._RECONCILE_ATLANDI_LOGGED.clear()
    yield
    loop._RECONCILE_ATLANDI_LOGGED.clear()


def _mutabakat_yaz(tarih: str) -> None:
    """Son BAŞARILI mutabakatın damgası."""
    store.write_json("broker_reconcile.json", {"date": tarih, "position_drift": False})


def _alarmlar(monkeypatch) -> list:
    yakalanan: list = []
    monkeypatch.setattr(obs, "alarm", lambda token, message, **f: yakalanan.append(
        {"token": token, "message": message, **f}))
    return yakalanan


# --- ASIL SÖZLEŞME ---------------------------------------------------------------

def test_ustuste_IKI_islem_gunu_atlanirsa_ALARM(monkeypatch):
    """Son mutabakat 19 Ağu, işlenen seans 21 Ağu → arada 2 işlem günü → alarm."""
    a = _alarmlar(monkeypatch)
    _mutabakat_yaz("2026-08-19")
    loop._reconcile_gunu_atlandi("noop", D_CUMA, takvim=TAKVIM)
    assert a, "mutabakat 2 işlem günüdür koşmuyor ve hiçbir alarm yok — 19 günlük pencere yeniden mümkün"
    assert a[0]["token"] == "MECHANISM_STALE", f"beklenmeyen token: {a[0]['token']}"
    assert a[0].get("gun") == 2, f"bayatlık günü yanlış ölçüldü: {a[0].get('gun')}"


def test_TEK_gun_atlama_alarm_URETMEZ(monkeypatch):
    """Bir gün atlamak NORMALDİR (EOD kadansı bilinçli). Alarm eşiği aşınca yanar —
    yoksa her gün öten bir alarm, alarm olmaktan çıkar."""
    a = _alarmlar(monkeypatch)
    _mutabakat_yaz("2026-08-20")
    loop._reconcile_gunu_atlandi("noop", D_CUMA, takvim=TAKVIM)
    assert not a, f"tek gün atlamada alarm bastı — gürültü üretir: {a}"


def test_HAFTA_SONU_yanlis_alarm_URETMEZ(monkeypatch):
    """AYIRT EDİCİ TEST — takvim günüyle yazılmış bir eşik BURADA düşer.
    Cuma mutabakat + Pazartesi atlama = 3 takvim günü, 1 İŞLEM günü. Alarm YOK."""
    a = _alarmlar(monkeypatch)
    _mutabakat_yaz(D_CUMA)
    loop._reconcile_gunu_atlandi("noop", D_PZT, takvim=TAKVIM)
    assert not a, f"hafta sonu boşluğunu bayatlık sandı — her pazartesi öter: {a}"


def test_AYNI_GUN_mutabakat_varsa_alarm_YOK(monkeypatch):
    """TAUTOLOJİ KONTROLÜ: çivi her çağrıda ötüyor olsaydı yukarıdakiler de geçerdi."""
    a = _alarmlar(monkeypatch)
    _mutabakat_yaz(D_CUMA)
    loop._reconcile_gunu_atlandi("noop", D_CUMA, takvim=TAKVIM)
    assert not a, f"mutabakat bugün koşmuşken alarm bastı: {a}"


# --- UYDURMA YASAĞI --------------------------------------------------------------

def test_OLCULEMEZSE_alarm_YOK_ve_BEYANLI(monkeypatch):
    """Takvim verilmediyse mesafe ÖLÇÜLEMEZ. Uydurulmaz, sessizce de yutulmaz:
    alarm basılmaz ama olay `bayat_gun=None` + nedenini taşır."""
    a = _alarmlar(monkeypatch)
    _mutabakat_yaz("2026-08-19")
    loop._reconcile_gunu_atlandi("noop", D_CUMA)          # takvim YOK
    assert not a, "ölçülemeyen mesafeden alarm uyduruldu"
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "reconcile_atlandi"]
    assert ev, "olay hiç basılmadı"
    assert ev[-1].get("bayat_gun") is None, "ölçülemeyen mesafe sayı gibi yazıldı"
    assert ev[-1].get("bayat_neden"), "ölçülemedi ama NEDENİ yazılmadı (YASA 4)"


def test_MUTABAKAT_HIC_KOSMAMISSA_alarm(monkeypatch):
    """Dosya yoksa mutabakat HİÇ koşmamıştır — bu en yüksek sesli hâldir, susulamaz."""
    a = _alarmlar(monkeypatch)
    loop._reconcile_gunu_atlandi("noop", D_CUMA, takvim=TAKVIM)
    assert a, "mutabakat hiç koşmamış ve alarm yok"
    assert a[0]["token"] == "MECHANISM_STALE"


# --- MEVCUT DAVRANIŞ KORUNUR ------------------------------------------------------

def test_ALARM_gun_basina_BIR_kez(monkeypatch):
    """`noop` dalı her gün-içi poll'da vurur. Alarm da tekilleşmeli, yoksa defter dolar."""
    a = _alarmlar(monkeypatch)
    _mutabakat_yaz("2026-08-19")
    for _ in range(4):
        loop._reconcile_gunu_atlandi("noop", D_CUMA, takvim=TAKVIM)
    assert len(a) == 1, f"alarm {len(a)} kez bastı — tekilleştirme bozuk"


def test_AYNA_YOKKEN_alarm_YOK(monkeypatch):
    """İç broker modunda ayna yoktur; 'mutabakat bayat' demek olmayan bir borcu alarmlamaktır."""
    a = _alarmlar(monkeypatch)
    monkeypatch.setattr(config, "BROKER", "internal", raising=False)
    loop._reconcile_gunu_atlandi("noop", D_CUMA, takvim=TAKVIM)
    assert not a, f"ayna yokken alarm bastı: {a}"


def test_UC_DAL_DA_TAKVIMI_GECIRIYOR():
    """KABLO KANITI — mekanizmanın ölü doğmadığı.

    `takvim` geçirilmezse `_mutabakat_bayatligi` dürüstçe `(None, neden, False)` döner ve alarm
    HİÇ ötmez. Yani bir çağrı yerinde parametreyi unutmak, bu turda kapatılan 19 günlük pencereyi
    O DAL İÇİN geri açar — ve hiçbir şey kırılmadığı için kimse fark etmez. Bu depoda emsali var:
    v288 çivisinin ilk sürümü bileşik yazımı göremediği için 15 yalancı pozitif vermişti; buradaki
    risk tersi ama aynı sınıf — sessiz bir YALANCI NEGATİF.
    """
    import inspect
    src = inspect.getsource(loop.daily_cycle)
    for sinif in ("noop", "waiting_for_universe", "refused_regressive"):
        assert f'_reconcile_gunu_atlandi("{sinif}", dstr, takvim=' in src, (
            f"`{sinif}` dalı takvimi GEÇİRMİYOR — o dalda bayatlık ölçülemez ve alarm ölü doğar")

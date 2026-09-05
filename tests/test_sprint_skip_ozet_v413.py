"""v413 — `sprint_cadence_skip` GÜNLÜK ÖZET + DEĞİŞİNCE-YAZ mandalı (TSK-141, 2026-09-05).

NEDEN VAR (ÖLÇÜM, A1 keşfi TSK-141 brief'inde): `meridian/sprint.py::maybe_start` her
`kos=False` kararında bu olayı KOŞULSUZ yazıyordu — 280-284 satır/gün, ardışık çiftlerin %98,2'si
`ts` hariç birebir aynı. TEK okuyucu `ops/bekci_tarama.py` (`_takili_tara` + `_duran_tara`) "her
pollde bir satır" kadansına bağımlıydı — mandal TEK BAŞINA ikisini kırardı (Yasa 6: üretilen bir
satır okunamaz hâle gelirdi). O yüzden bu turda ÖNCE okuyucu (bekci_tarama, iki fikstürle: eski
ham desen + yeni özet desen AYNI hükmü verir), SONRA yazan (`sprint._skip_ozetle`) değişti.

DÖRT ÇİVİ, D4 SÖZLEŞMESİ:
  (1) aynı sebep 100 poll → 1 ilk satır + 0 ek.
  (2) sebep değişince hemen satır + öncekinin özeti.
  (3) gün dönüşünde özet toplam_n doğru.
  (4) bekci_tarama yeni desenle kertik/duran AYNI hükmü verir (iki fikstür, iki alt test).

MUTASYON (D4 madde 5, kalıcı test DEĞİL — CLAUDE.md §6): "çivi yeşili kanıt değildir" ilkesi bu
turda ELLE doğrulandı: `_skip_ozetle`in mandal dalı (aynı-gün-aynı-sebep → `[]`) geçici olarak
`[{"ozet": False}]` döndürecek şekilde bozulup test (1) kırmızıya düşürüldü (100 poll'ün HEPSİ
yazım üretti), sonra GERİ ALINDI. Kanıt bu dosyanın DIŞINDA (rapor metninde) — kalıcı bir test
dosyaya sızmadı.

CANLI STATE'E YAZILMAZ: `_skip_ozetle` yalnız süreç-içi `sprint._SKIP_SON`e dokunur, `obs.log`
çağırmaz (o iş `maybe_start`in KENDİSİNDE, burada sınanmaz — üretim yolu v239'da zaten çivili:
`test_skip_olayi_yetim_ve_tetigi_AYRI_tasir`). `_mandal_temiz` fikstürü `_SKIP_SON`i her testten
ÖNCE/SONRA temizler (tests/conftest.py'deki `_MODUL_DURUMLARI` global sıfırlamasının YANI SIRA —
burada AYRICA ELLE temizlenir çünkü bazı testler `_SKIP_SON`u özenle SIFIRDAN kurmak ister).

`from __future__ import annotations` BİLEREK YOK (v333'ünkinden AYRI ama AKRABA bir tuzak,
ÖLÇÜLDÜ bu dosya yazılırken): bu satır AÇIKSA, aşağıdaki `compile(...)` çağrısı `dont_inherit`
vermediği için CPython derleyici bayrağını (CO_FUTURE_ANNOTATIONS) exec EDİLEN `ops/bekci_tarama.py`
KAYNAĞINA SIZDIRIR — o dosyanın KENDİSİ bu future'ı taşımasa BİLE `Kayit` dataclass'ının alan
tipleri STRING'e döner ve Python 3.12'nin dataclass işleyicisi `sys.modules.get(cls.__module__)`i
arar; modül `sys.modules`e KAYIT OLMADAN yüklendiği için `None` döner ve `AttributeError` patlar.
ÖLÇÜLDÜ: hem pytest altında HEM düz bir `.py` betiğinde AYNI şekilde patlar (bayrak sızıntısı
çağıran ÇERÇEVEYE bağlı, harness'e değil) — v333 bu future'ı hiç taşımadığı için bu sınıfa hiç
girmiyordu, tesadüfen değil YAPISAL olarak bağışıktı."""

import datetime as dt
import json
import pathlib

import pytest

from meridian import sprint
from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/bekci_tarama.py"
UTC = dt.timezone.utc


def _yukle():
    """`ops/bekci_tarama.py`yi `sys.modules`e KAYIT OLMADAN yükler — v333 ile AYNI kalıp.

    KAYNAKTAN COMPILE EDİLİR, `exec_module` İLE DEĞİL (v333'ün gerekçesi aynen geçerli: depo
    kalıbı `.pyc`nin mtime-SANİYE geçerlilik kontrolüne düşer ve hızlı bir düzenle-geri-yükle
    turunda bayat bayt-kodu ölçebilir).

    ARTIK (2026-09-05, aynı gün — v334 §B3): gövde `tests.conftest.betikten_modul_yukle`
    (`dont_inherit=True`); başlıktaki sızıntı anlatısı tarihçedir, artık bu dosyanın future'sız
    kalmasına YASLANMAZ — koruma yardımcıdadır ve v334 §B4 onu davranışla çiviler."""
    assert BETIK.exists(), f"{BETIK} YOK"
    return betikten_modul_yukle(BETIK, "bekci_tarama_v413")


@pytest.fixture(autouse=True)
def _mandal_temiz():
    sprint._SKIP_SON.clear()
    yield
    sprint._SKIP_SON.clear()


def _epoch(iso: str) -> float:
    return dt.datetime.fromisoformat(iso).replace(tzinfo=UTC).timestamp()


def _ts(epoch: float) -> str:
    return dt.datetime.fromtimestamp(epoch, UTC).isoformat(timespec="seconds")


# ============================ (1) AYNI SEBEP: 1 İLK SATIR + 0 EK ================================

def test_ayni_sebep_100_poll_bir_ilk_satir_sifir_ek():
    """`sprint_cadence_skip{sebep:"mesgul:canli_arama"}` 4+ gün HER döngüde tekrar eden ÖLÇÜLMÜŞ
    canlı arızanın (TSK-141 brief keşfi) doğrudan karşılığı: aynı sebep tekrar ettikçe defter
    TEK bir ilk satırdan sonra SESSİZ kalmalı."""
    sebep = "mesgul:canli_arama"
    t0 = _epoch("2026-09-05T10:00:00")
    ilk = sprint._skip_ozetle(sebep, now=t0)
    assert ilk == [{"ozet": False}], ilk
    for i in range(1, 100):
        sonra = sprint._skip_ozetle(sebep, now=t0 + i)
        assert sonra == [], f"poll {i}: mandal susmadı — {sonra}"


# ============================ (2) SEBEP DEĞİŞİNCE: HEMEN + ÖNCEKİNİN ÖZETİ =======================

def test_sebep_degisince_hemen_satir_ve_oncekinin_ozeti():
    t0 = _epoch("2026-09-05T10:00:00")
    assert sprint._skip_ozetle("A", now=t0) == [{"ozet": False}]
    # A iki kez daha tekrarlanır (aynı UTC günü) — sessiz birikim.
    assert sprint._skip_ozetle("A", now=t0 + 300) == []
    assert sprint._skip_ozetle("A", now=t0 + 600) == []
    # sebep B'YE DEĞİŞİR: iki AYRI satır — önce A'nın özeti, sonra B'nin anında satırı.
    degisim = sprint._skip_ozetle("B", now=t0 + 900)
    assert degisim == [
        {"ozet": True, "gun": "2026-09-05", "sebep": "A", "toplam_n": 2,
         "ilk_ts": _ts(t0), "son_ts": _ts(t0 + 600)},
        {"ozet": False},
    ], degisim
    # B artık AKTİF mandal — tekrarı yine sessiz.
    assert sprint._skip_ozetle("B", now=t0 + 950) == []


# ============================ (3) UTC GÜN DÖNÜŞÜ: ÖZET toplam_n DOĞRU ============================

def test_gun_donusunde_ozet_toplam_n_dogru():
    sebep = "tetik_yok(gun=3<7, taze=0<5)"
    gun1_ilk = _epoch("2026-09-05T23:00:00")
    assert sprint._skip_ozetle(sebep, now=gun1_ilk) == [{"ozet": False}]
    gun1_son = gun1_ilk
    for dk in (10, 20, 30):
        gun1_son = gun1_ilk + dk * 60
        assert sprint._skip_ozetle(sebep, now=gun1_son) == []
    # GÜN DÖNER (2026-09-06 00:1x), sebep AYNI kalır: yalnız BİTEN günün özeti düşer — sebep
    # değişmediği için ANINDA satır YOK (session_refresh'in gün-dönüşü davranışıyla aynı sınıf).
    gun2_ilk = _epoch("2026-09-06T00:10:00")
    donus = sprint._skip_ozetle(sebep, now=gun2_ilk)
    assert donus == [{"ozet": True, "gun": "2026-09-05", "sebep": sebep, "toplam_n": 3,
                      "ilk_ts": _ts(gun1_ilk), "son_ts": _ts(gun1_son)}], donus
    # gün2'nin sayacı biriktirmeye devam eder — bu poll zaten gün2'nin İLK (sayılan) olayıydı.
    assert sprint._skip_ozetle(sebep, now=gun2_ilk + 60) == []


# ============================ (4) BEKÇİ_TARAMA: HAM ↔ ÖZET AYNI HÜKÜM ============================

def _satir(ts_iso, olay, seviye="info", **alanlar):
    return json.dumps({"ts": ts_iso, "level": seviye, "event": olay, **alanlar},
                      ensure_ascii=False)


def _yaz(yol, satirlar):
    yol.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return yol


def _ham_defter_kur(tmp_path, ad, gun_sayisi=6):
    """ESKİ (mandalsız) desen: saatlik kayıt, `gun_sayisi` gün boyunca AYNI sebep — canlının
    yüksek-frekans ham yayınının küçültülmüş bir benzeri (SINIFI değiştirmez, tam ölçek testi
    yalnız yavaşlatırdı)."""
    taban = dt.datetime(2026, 8, 30, tzinfo=UTC)
    s = []
    for g in range(gun_sayisi):
        for saat in range(24):
            an = taban + dt.timedelta(days=g, hours=saat)
            s.append(_satir(an.isoformat(), "sprint_cadence_skip",
                            sebep="mesgul:canli_arama", gecen_gun=g, taze_hipotez=0, yetim=True))
    return _yaz(tmp_path / ad, s)


def _ozet_defter_kur(tmp_path, ad, gun_sayisi=6):
    """YENİ (mandal) desen: AYNI çok-günlük durumu GERÇEK `sprint._skip_ozetle` çağrılarıyla
    üretir (elle uydurulmaz) — 1. gün anında satır, sonraki her gün dönüşünde bir önceki günün
    özeti. `_SKIP_SON` bu fonksiyondan ÖNCE VE SONRA temizlenir; üretim yolunun KENDİSİ sınanır,
    yeniden yazılmaz."""
    sprint._SKIP_SON.clear()
    taban = dt.datetime(2026, 8, 30, tzinfo=UTC)
    sebep = "mesgul:canli_arama"
    s = []
    for g in range(gun_sayisi):
        an = taban + dt.timedelta(days=g, hours=1)
        for yazim in sprint._skip_ozetle(sebep, now=an.timestamp()):
            if yazim.get("ozet"):
                s.append(_satir(an.isoformat(), "sprint_cadence_skip", **yazim))
            else:
                s.append(_satir(an.isoformat(), "sprint_cadence_skip", sebep=sebep,
                                gecen_gun=g, taze_hipotez=0, yetim=True, ozet=False))
    sprint._SKIP_SON.clear()
    return _yaz(tmp_path / ad, s)


def test_bekci_tarama_ham_ve_ozet_desen_ayni_takili_hukmunu_verir(tmp_path):
    mod = _yukle()
    taban = dt.datetime(2026, 8, 30, tzinfo=UTC)
    simdi = (taban + dt.timedelta(days=6)).isoformat()
    ham = mod.tara(gun=6, defter=_ham_defter_kur(tmp_path, "ham_takili.jsonl"), simdi=simdi)
    ozet = mod.tara(gun=6, defter=_ozet_defter_kur(tmp_path, "ozet_takili.jsonl"), simdi=simdi)
    hedef = "sprint_cadence_skip[mesgul:canli_arama]"
    assert hedef in [k["ad"] for k in ham["takili"]], ham["takili"]
    assert hedef in [k["ad"] for k in ozet["takili"]], ozet["takili"]
    # KAYNAK ayrışması GÖRÜNÜR: ham türetilmiş yolu (`_imza`), özet GÜN-bazlı mandal yolunu
    # kullanır — ikisi FARKLI mekanizma, AYNI hükme varır.
    ham_kalem = next(k for k in ham["takili"] if k["ad"] == hedef)
    ozet_kalem = next(k for k in ozet["takili"] if k["ad"] == hedef)
    assert ham_kalem["kanit"]["kaynak"] == "turetilmis", ham_kalem
    assert ozet_kalem["kanit"]["kaynak"] == "ozet_mandali", ozet_kalem
    # 6 GÜNLÜK fikstür 6 FARKLI günde bir satır bırakır (day0 anında + day1..day5 özet) — ham
    # yolun 144 HAM kaydına karşı özet yolun ölçtüğü GÜN SAYISI budur.
    assert ozet_kalem["kanit"]["gun_sayisi"] == 6, ozet_kalem


def test_bekci_tarama_ham_ve_ozet_desen_ayni_duran_hukmunu_verir(tmp_path):
    """AYNI 6 günlük geçmiş, sonra SESSİZLİK: hem ham (yüksek frekans → durur) hem özet (mandal
    → gün bazlı 'kesildi') aynı olayı `duran` listesine düşürmeli — farklı mekanizma, aynı hüküm."""
    mod = _yukle()
    taban = dt.datetime(2026, 8, 30, tzinfo=UTC)
    simdi = (taban + dt.timedelta(days=9)).isoformat()   # son kayıttan ~4 gün sonrası — sessizlik
    ham = mod.tara(gun=6, duran_gun=15, defter=_ham_defter_kur(tmp_path, "ham_duran.jsonl"),
                   simdi=simdi)
    ozet = mod.tara(gun=6, duran_gun=15, defter=_ozet_defter_kur(tmp_path, "ozet_duran.jsonl"),
                    simdi=simdi)
    assert "sprint_cadence_skip" in [k["ad"] for k in ham["duran"]], ham["duran"]
    assert "sprint_cadence_skip" in [k["ad"] for k in ozet["duran"]], ozet["duran"]
    ham_kalem = next(k for k in ham["duran"] if k["ad"] == "sprint_cadence_skip")
    ozet_kalem = next(k for k in ozet["duran"] if k["ad"] == "sprint_cadence_skip")
    assert ozet_kalem["kanit"]["kaynak"] == "gun_bazli", ozet_kalem
    assert ozet_kalem["kanit"]["eksik_gunler"], ozet_kalem
    assert "kaynak" not in ham_kalem["kanit"], ham_kalem

"""NABIZ İŞ BİTİMİNE DEĞİL, İPLİK CANLILIĞINA BAĞLANIR · v302

VAKA (2026-08-25). `MECHANISM_STALE ... hermes_poll — 0.5 sa (pencere 0.5 sa)` alarmı
2026-08-06'dan beri günde bir kez ötüyordu ve ÜÇ KEZ yanlış teşhis edildi. Çok-mercekli
soruşturma (5 bulucu + 3 şüpheci; üç şüphecinin ÜÇÜ de ilk hipotezi çürüttü) şunu ölçtü:

  · `beat("hermes_poll")` YALNIZ 3 yerde ve hepsi `hermes_runtime.py` (176, 193, 488).
    `reflect.py`de ve `hermes.py`de HİÇ YOK.
  · Isınma dalında İLK nabza kadar üç ağır faz NABIZSIZ koşuyor:
      (1) `prefill_incumbents` havuz bekleyişi — TEK blokta `_cf.wait(timeout=1800)`
      (2) atalet sonrası sıralı incumbent yedeği (canlıda ölçülen: 5065 sn)
      (3) `_parallel_prefill_probes` havuz bekleyişi — 1800 sn daha
    (1) YAPISAL olarak yamanamıyordu: `prefill_incumbents` hermes_runtime.py:167'de
    çağrılıyor, `_nabiz` ise :170'te TANIMLANIYOR — nabız daha doğmamış.
  · `HAVUZ_ATALET_SN = 1800` (reflect.py) ile `EXPECTED["hermes_poll"] = 1800`
    (watchdog.py) BİREBİR EŞİT → havuz ataleti her çarptığında pencere TANIM GEREĞİ
    tam olarak doluyor; bayat-geçiş garanti.
  · CANLI KANIT: 2026-08-24'te alarm 01:59:48'de düştü, `arama_havuzu_zaman_asimi
    biten=0` olayı 02:00:08'de — 20 sn SONRA. Sonda döngüsü hiç başlamamıştı.

ÇÖZÜM SINIFI: pencereyi genişletmek ya da alarmı susturmak DEĞİL — `watchdog.EXPECTED`
tablosundaki `hermes_poll` yorumu ikisini de açıkça reddediyor ("pencereyi ısınmaya göre
genişletmek yanlış olurdu"). Nabız artık "bir iş bitti" değil "iplik canlı ve bekliyor" diyor: havuz
bekleyişi küçük kuantumlara bölündü ve her kuantumda canlılık geri-çağırması ateşleniyor.
TOPLAM-ATALET YASASI DEĞİŞMEDİ — kurtarma hâlâ HAVUZ_ATALET_SN'de tetikleniyor.
"""
from __future__ import annotations

import concurrent.futures as cfut
import inspect
import re
import time

import pytest

from meridian import reflect, watchdog


# --------------------------------------------------- havuz bekleyişinde nabız

def _havuz(monkeypatch, is_suresi: float, atalet: float, kuantum: float):
    """Hızlı bir havuz kurgusu: iş `is_suresi` kadar uyur, tavan ve kuantum küçültülür."""
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", atalet)
    monkeypatch.setattr(reflect, "HAVUZ_NABIZ_SN", kuantum)
    monkeypatch.setattr(reflect, "_pool_probe_job",
                        lambda j: (time.sleep(is_suresi), ("k", {"v": 1}))[1])


def test_hicbir_is_bitmezken_nabiz_ATILIYOR(monkeypatch):
    """ASIL ÇİVİ: havuz 'atalet' boyunca sıfır iş bitirse bile iplik canlılığını bildirir."""
    _havuz(monkeypatch, is_suresi=5.0, atalet=0.30, kuantum=0.05)
    vurus = []
    with cfut.ThreadPoolExecutor(max_workers=1) as ex:
        with pytest.raises(reflect._HavuzAtaleti):
            list(reflect._havuz_sonuclari(ex, [{"i": 1}], canlilik=lambda: vurus.append(1)))
    assert len(vurus) >= 4, (
        f"havuz bekleyişi boyunca yalnız {len(vurus)} nabız atıldı — kuantum 0.05, tavan 0.30 "
        "iken en az 4 beklenir; nabız hâlâ İŞ BİTİMİNE bağlı")


def test_toplam_atalet_YASASI_degismedi(monkeypatch):
    """Kuantumlara bölmek kurtarma eşiğini KAYDIRMAMALI: atalet hâlâ HAVUZ_ATALET_SN'de patlar."""
    _havuz(monkeypatch, is_suresi=5.0, atalet=0.30, kuantum=0.05)
    # SÜRE `with` BLOĞUNUN İÇİNDE ölçülür: blok çıkışı koşan işi (5 sn) join eder ve dışarıdan
    # ölçmek o beklemeyi ataletin üstüne yazardı — ölçüm bağlamı tuzağının test hâli.
    with cfut.ThreadPoolExecutor(max_workers=1) as ex:
        t0 = time.monotonic()
        with pytest.raises(reflect._HavuzAtaleti):
            list(reflect._havuz_sonuclari(ex, [{"i": 1}], canlilik=lambda: None))
        gecen = time.monotonic() - t0
    assert 0.30 <= gecen < 1.2, (
        f"atalet {gecen:.2f} sn'de patladı — tavan 0.30 sn; kuantumlama eşiği kaydırmış")


def test_is_bitince_atalet_SIFIRLANIR(monkeypatch):
    """İlerleyen havuz ASLA kesilmez (dosyadaki YASA): biten her iş sayacı sıfırlar."""
    _havuz(monkeypatch, is_suresi=0.01, atalet=0.30, kuantum=0.05)
    with cfut.ThreadPoolExecutor(max_workers=2) as ex:
        sonuc = list(reflect._havuz_sonuclari(ex, [{"i": i} for i in range(6)],
                                              canlilik=lambda: None))
    assert len(sonuc) == 6, f"ilerleyen havuz kesildi: {len(sonuc)}/6"


def test_nabiz_patlarsa_havuz_DUSMEZ(monkeypatch):
    """Nabız yazımı (disk) düşerse aramanın kendisi kurban edilmez — YASA 4 sınıfı."""
    _havuz(monkeypatch, is_suresi=0.01, atalet=0.30, kuantum=0.05)

    def _kotu():
        raise OSError("disk dolu")

    with cfut.ThreadPoolExecutor(max_workers=2) as ex:
        sonuc = list(reflect._havuz_sonuclari(ex, [{"i": i} for i in range(3)], canlilik=_kotu))
    assert len(sonuc) == 3, "nabız hatası aramayı öldürdü — telemetri arızası ölçümü silmemeli"


def test_canlilik_gecirilmezse_eski_davranis(monkeypatch):
    """Geriye uyum: `canlilik` verilmeyen çağrı (testler, başka tüketiciler) çalışmaya devam eder."""
    _havuz(monkeypatch, is_suresi=0.01, atalet=0.30, kuantum=0.05)
    with cfut.ThreadPoolExecutor(max_workers=2) as ex:
        assert len(list(reflect._havuz_sonuclari(ex, [{"i": 1}]))) == 1


# ----------------------------------------------- kör faz artık yamanabilir mi

def test_kuantum_bekci_penceresinden_KUCUK():
    """Nabız kuantumu bekçi penceresinden belirgin biçimde küçük olmalı; yoksa kör faz geri gelir.
    `HAVUZ_ATALET_SN == EXPECTED['hermes_poll']` eşitliği KORUNUYOR (o bir tesadüf değil, iki
    ayrı türetim) — zararsız hâle getiren şey eşitliği kırmak değil, ARADA nabız atmaktır."""
    pencere = watchdog.EXPECTED["hermes_poll"]
    assert reflect.HAVUZ_NABIZ_SN * 4 <= pencere, (
        f"kuantum {reflect.HAVUZ_NABIZ_SN} sn, pencere {pencere} sn — bekleyiş boyunca en az "
        "dört nabız sığmalı ki tespit gecikmesi (300 sn poll) altında kalsın")


def test_prefill_incumbents_NABZI_ALIYOR():
    """(1) numaralı kör faz: `prefill_incumbents` canlılık geri-çağırması kabul etmeli."""
    imza = inspect.signature(reflect.prefill_incumbents)
    assert "canlilik" in imza.parameters, (
        "prefill_incumbents canlılık kancası almıyor — havuz bekleyişi hâlâ nabızsız "
        f"(imza: {imza})")


def test_arama_NABZI_ALIYOR_ve_onfaza_GECIRIYOR():
    """(3) numaralı kör faz: arama, sonda ön-doldurmasına canlılığı geçirmeli."""
    assert "canlilik" in inspect.signature(reflect.coordinate_descent_search).parameters
    assert "canlilik" in inspect.signature(reflect._parallel_prefill_probes).parameters
    src = inspect.getsource(reflect.coordinate_descent_search)
    assert "canlilik=canlilik" in src or "canlilik," in src, (
        "arama canlılığı alıyor ama ön-doldurmaya GEÇİRMİYOR — kör faz açık kalır")


def test_hermes_isinmasi_prefill_ONCESINDE_nabiz_atiyor():
    """YAPISAL ÇİVİ. Eski kodda `_nabiz` (satır 170) `prefill_incumbents`ten (satır 167) SONRA
    tanımlanıyordu — o fazda nabız atmak imkânsızdı. Kaynak SIRASI bunu bir daha yapmamalı."""
    from meridian import hermes_runtime
    src = inspect.getsource(hermes_runtime)
    i_tanim = src.find("def _nabiz(")
    i_prefill = src.find("reflect.prefill_incumbents(")
    assert i_tanim != -1 and i_prefill != -1, "çivinin çapaları kaynakta bulunamadı"
    assert i_tanim < i_prefill, (
        "`_nabiz` hâlâ `prefill_incumbents` çağrısından SONRA tanımlanıyor — o faz yapısal "
        "olarak nabızsız kalır (2026-08-24 01:59:48 alarmının tam sebebi)")
    # ZAYIF ÇİVİ DÜZELTMESİ (mutasyonla yakalandı): düz `"canlilik=" in src` yetmiyordu —
    # arama çağrısındaki kanca kaldığı için prefill'in kancası sökülünce çivi SUSUYORDU.
    # Artık İKİ çağrı da AYRI AYRI çivili.
    m = re.search(r"reflect\.prefill_incumbents\((.*?)\)", src, re.S)
    assert m and "canlilik=" in m.group(1), (
        "`prefill_incumbents` çağrısı canlılık kancasını GEÇİRMİYOR — (1) numaralı kör faz açık")
    m2 = re.search(r"coordinate_descent_search\((.*?)record_session", src, re.S)
    assert m2 and "canlilik=" in m2.group(1), (
        "arama çağrısı canlılık kancasını GEÇİRMİYOR — (3) numaralı kör faz açık")

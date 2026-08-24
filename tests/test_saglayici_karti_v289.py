"""SAĞLAYICI KARTI EKSİKSİZ Mİ? — v289 (2026-08-25)

VAKA. Operatör bildirdi: "FMP'yi sağlayıcılarda göremiyorum, araçlarda ise FMP gerek
diyor." Ölçüm onu doğruladı ve ARIZA ARAYÜZDE DEĞİL ARKA UÇTAYDI:

  · `adapters/fmp.py` VAR, `health()` sunuyor, iki anahtar yuvası var
    (`FMP_API_KEY` + rotasyonlu `FMP_API_KEY_2`), günlük kota muhasebesi tutuyor.
  · `skills.py` araçları `fmp.available()` ile KAPILIYOR — yani "FMP gerek" yazısı
    doğru ve o araçlar kapalı.
  · `api.py::_saglayicilar` ise ALTI SATIR üretiyordu ve FMP onlardan biri DEĞİLDİ.

Bedeli ölçüldü: aynı teşhis gövdesi `integrity.production.starved` altında
`fmp_source` diyor ("anahtar var ama üretmiyor — 402 Payment Required") ve
`pipeline.fmp_usage` 2026-08-23 için 43 çağrı / 43 hata sayıyor. Yani sağlayıcı
ÇALIŞMIYORDU, sistem bunu BİLİYORDU, ve en çok bakılan kart onu HİÇ göstermiyordu.

Aynı sayımda `adapters/constituents` de kartta yoktu (S&P 500 üyeliği; evren
sapması ona bağlı, Wikipedia yolu bu kurulumda 403 alıyor).

ÇİVİNİN İDDİASI TEK SATIRDA: `health()` sunan bir adaptör bir SAĞLAYICIDIR ve
sağlayıcı kartında satırı OLMAK ZORUNDADIR. Kartta olmayan bir sağlayıcı,
bozulduğunda kimsenin bakmadığı bir yerde bozulur.
"""
from __future__ import annotations

import inspect
import pkgutil
from importlib import import_module

from meridian import api
from meridian import adapters as _adapters


def _saglik_sunan_adaptorler() -> set[str]:
    """`health()` sunan adaptör modülleri — sağlayıcı olmanın ölçülebilir tanımı.

    NEDEN BU TANIM: "sağlayıcı" bir liste değil bir SÖZLEŞMEdir — sağlık sayacı tutan
    modül, dışarıya bağlı ve bozulabilir demektir. Elle tutulan bir ad listesi
    olsaydı, bir sonraki adaptör eklendiğinde yine sessizce dışarıda kalırdı; bu
    çivinin var olma sebebi tam olarak o.
    """
    adlar: set[str] = set()
    for m in pkgutil.iter_modules(_adapters.__path__):
        mod = import_module(f"meridian.adapters.{m.name}")
        f = getattr(mod, "health", None)
        if callable(f) and not inspect.isclass(f):
            adlar.add(m.name)
    return adlar


def _kart_adlari() -> set[str]:
    """`_saglayicilar` gövdesinde geçen satır adları — KAYNAKTAN okunur, çağrılmaz.

    Fonksiyonu çağırmak adaptörlerin `health()`ini tetikler ve bazıları süreç-içi
    durum kurar; denetim bir yan etki üretmemeli.
    """
    kaynak = inspect.getsource(api._saglayicilar)
    import re
    return set(re.findall(r'_saglayici_satiri\(\s*"([a-z_]+)"', kaynak)) | \
           set(re.findall(r'\{"ad":\s*"([a-z_]+)"', kaynak))


# `health()` sunan adaptör adı ↔ kartta göründüğü ad. Ayrışabilirler ve ayrışmaları
# MEŞRUDUR: Alpaca'nın iki taşıması ayrı satır (`alpaca_veri` / `alpaca_ticaret`),
# üyelik kaynağı ise ürünün adıyla (`uyelik`) okunuyor — "constituents" operatörün
# diline ait değil. Eşleme burada AÇIK tutulur ki bir sonraki ad değişikliği çiviyi
# sessizce yeşil bırakmasın.
AD_ESLEMESI: dict[str, str] = {
    "constituents": "uyelik",
}


def test_saglik_sunan_her_adaptorun_kartta_satiri_VAR():
    adaptorler = _saglik_sunan_adaptorler()
    assert adaptorler, "hiç adaptör bulunamadı — tarayıcı bayat"
    kart = _kart_adlari()
    eksik = sorted(a for a in adaptorler if AD_ESLEMESI.get(a, a) not in kart)
    assert not eksik, (
        f"`health()` sunan ama sağlayıcı kartında SATIRI OLMAYAN adaptör: {eksik}\n"
        "Kartta olmayan bir sağlayıcı, bozulduğunda kimsenin bakmadığı yerde bozulur — "
        "FMP tam bunu yaşadı (43/43 çağrı 402 ile düştü, kart bunu hiç göstermedi). "
        "`api.py::_saglayicilar`a satırını ekle; adı farklıysa AD_ESLEMESI'ne yaz.")


def test_fmp_kartta_ve_anahtar_kota_kullanim_AYRI_alanlarda():
    """FMP satırı üç ayrı soruyu AYRI taşımalı: anahtar var mı · kota kapatmış mı · günün muhasebesi.

    Üçünü tek bayrağa indirmek "anahtar YOK" ile "anahtar VAR ama plan kapsamıyor"u
    aynı hâle sokar — ve canlıda geçerli olan İKİNCİSİ (402 Payment Required).
    Operatör ilkini okusaydı anahtarı yeniden girerdi ve hiçbir şey değişmezdi.
    """
    kaynak = inspect.getsource(api._saglayicilar)
    assert '_saglayici_satiri("fmp"' in kaynak, "FMP satırı kartta yok"
    for alan in ('"anahtar"', '"kota_blokli"', '"kullanim"'):
        assert alan in kaynak, f"FMP satırının `ek` bloğunda {alan} yok — üç soru ayrışmamış"

"""v318 — ATALET TAVANI ÖLÇÜLEN İŞ SÜRESİNİN ALTINDAYDI: sağlıklı havuz her turda öldürüldü.

ÖLÇÜLEN OLGU (canlı A1, 2026-08-25 adliyesi). `arama_havuzu_zaman_asimi` olaylarının
TAMAMINDA — 2026-08-12'den beri 61 olay — `biten=0`. Bir kez bile bir iş bitmemiş. Sebep
kilitlenme/açlık/OOM DEĞİL; tavan tek bir işten KISA:

    iş başına walk-forward, üç bağımsız ölçüm:
      · 45 başarılı `parallel_probes_prefilled` turu (duvar×işçi/n) ....  2279-3042 sn
      · ardışık `hermes_search_probe` farkı (sıralı yol, 08-17 + 08-21)   2487-3185 sn
      · reflect.py'nin kendi notu (5065 sn / 2 walk-forward) ..........   2532 sn
    ESKİ TAVAN ......................................................    1800 sn

Tek iş tavanın 1,3-1,8 katı sürdüğü için ilk bitiş HİÇBİR ZAMAN tavana yetişemez: `biten=0`
bir arıza belirtisi değil, ARİTMETİK ZORUNLULUKTU. Havuz 2026-08-12'ye kadar ÇALIŞIYORDU
(son başarı 08-12T07:40, n=10) — tavan o gün indi (`becb03b`), ilk aşım 08-12T11:40'ta geldi
ve mekanizma bir daha hiç sonuç üretmedi.

ESKİ TÜRETİM NEREDE KAYDI: gerekçe "incumbent-walk ~90 sn ÖLÇÜLÜDÜR" diyordu ve 1800'ü onun
20 katı olarak kuruyordu. O 90 sn `hermes.py`de PANONUN bekleme süresi için düşülmüş bir nottur
ve BAŞKA bir hesabı anlatır; havuz işi 251 sembollük SONDA walk-forward'ıdır. Doğru sayı
ölçülmemiş değildi — `events.jsonl`da 94 satırdı, bakılmamıştı.

ÇİVİ ÜÇ BACAKLI ve ortadaki bilerek DAVRANIŞSAL: sabit-karşılaştırması bir totoloji olurdu,
oysa canlı arıza bir ORAN arızasıydı. Ortadaki test gerçek (iş süresi, tavan) çiftini 1/10000
ölçekte GERÇEK `_havuz_sonuclari`ndan geçirir — tavan ölçülen işin altına indirilirse test
davranışla kırmızıya döner. Üçüncü bacak yasanın İPTAL EDİLMEDİĞİNİ sınar: gerçekten ölü bir
havuz hâlâ yakalanmalı (tavanı yükseltmek alarmı susturmak DEĞİLDİR — v313 jetonu yerinde)."""
from __future__ import annotations
import concurrent.futures as cfut
import time

import pytest

from meridian import reflect

# Yukarıdaki tablonun EN KÖTÜ gözlemi. Çivi buna karşı ölçer; ölçüm yenilenirse ikisi
# birlikte güncellenir (kaynaktaki sabit + buradaki beklenti).
OLCULEN_EN_UZUN_IS_SN = 3185.0


def test_tavan_olculen_is_suresini_KAPSAR():
    """Tavan, ölçülen EN UZUN tek işin altında olamaz — canlı arızanın birebir tanımı."""
    olculen = getattr(reflect, "HAVUZ_IS_SURESI_OLCULEN_SN", None)
    assert olculen is not None, (
        "reflect.py atalet tavanını hangi ÖLÇÜLEN iş süresinden türettiğini söylemiyor — "
        "`HAVUZ_IS_SURESI_OLCULEN_SN` yok. Türetimin dayanağı kaynakta adlandırılmadıkça "
        "eski '~90 sn' vakası (yanlış mekanizmadan alınan sayı) sessizce tekrar edebilir")
    assert olculen >= OLCULEN_EN_UZUN_IS_SN, (
        f"kaynaktaki ölçüm {olculen} sn, canlıda gözlenen en uzun iş {OLCULEN_EN_UZUN_IS_SN} sn")
    assert reflect.HAVUZ_ATALET_SN > olculen, (
        f"tavan {reflect.HAVUZ_ATALET_SN} sn, ölçülen tek iş {olculen} sn — tavan işten KISA "
        "olduğunda ilk bitiş tavana asla yetişemez ve `biten=0` aritmetik zorunluluk olur "
        "(canlıda 61 olayın 61'i)")


def test_gercek_ORAN_saglikli_havuzu_oldurmez(monkeypatch):
    """ASIL ÇİVİ: gerçek (iş, tavan) oranı 1/10000 ölçekte GERÇEK bekleyişten geçer.

    Sabit karşılaştırması değil DAVRANIŞ: tavan ölçülen işin altına inerse bu test, hangi
    sayılarla olursa olsun, canlıdaki `_HavuzAtaleti`nin aynısıyla kırmızıya döner."""
    olcek = 1.0 / 10000.0
    is_suresi = OLCULEN_EN_UZUN_IS_SN * olcek                 # ~0,32 sn
    tavan = reflect.HAVUZ_ATALET_SN * olcek                   # varsayılan tavan, aynı ölçekte
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", tavan)
    monkeypatch.setattr(reflect, "HAVUZ_NABIZ_SN", 0.05)
    monkeypatch.setattr(reflect, "_pool_probe_job",
                        lambda j: (time.sleep(is_suresi), (j["k"], {"v": 1}))[1])
    jobs = [{"k": "a"}, {"k": "b"}]
    with cfut.ThreadPoolExecutor(max_workers=1) as ex:   # tek işçi = en kötü hal (iş başına tam süre)
        sonuc = list(reflect._havuz_sonuclari(ex, jobs, canlilik=lambda: None))
    assert len(sonuc) == len(jobs), (
        f"tavan ({tavan:.3f} sn) ölçülen iş süresinin ({is_suresi:.3f} sn) altında kaldı — "
        "sağlıklı havuz sonuç veremeden öldürüldü, canlıdaki `biten=0` vakasının ta kendisi")


def test_yasa_IPTAL_EDILMEDI_gercekten_olu_havuz_hala_yakalanir(monkeypatch):
    """Tavanı yükseltmek yasayı kaldırmak DEĞİLDİR: hiç bitmeyen havuz hâlâ `_HavuzAtaleti`."""
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 0.30)
    monkeypatch.setattr(reflect, "HAVUZ_NABIZ_SN", 0.05)
    monkeypatch.setattr(reflect, "_pool_probe_job",
                        lambda j: (time.sleep(30.0), ("k", {"v": 1}))[1])
    with cfut.ThreadPoolExecutor(max_workers=1) as ex:
        with pytest.raises(reflect._HavuzAtaleti):
            list(reflect._havuz_sonuclari(ex, [{"k": "a"}], canlilik=lambda: None))

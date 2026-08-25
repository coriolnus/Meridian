"""KAPANMIŞ ŞEMA NEDENİ — "yazılım hatası" ile "tarihsel kayıp" AYRI CÜMLELERDİR · v299

VAKA (2026-08-25). `sieve` her `sema:` elemesi için şunu yazıyordu:

    "Bu bir piyasa filtresi DEĞİL, yazılım hatasıdır: satır beklenen alanı taşımıyor
     ve hesaptan sessizce düşüyor."

`sema:plan_join_yok×535` için o cümle ARTIK YANLIŞ ve operatörü kapalı bir kusurun
peşine gönderiyor. Ölçüldü:
  · sebep 2026-08-23'te KAPATILDI (kırpma tavanı işleme dönüşmüş planları süpürüyordu)
  · kayıp 535 satır GERİ GELMEZ: yedeklerin en eskisi 43'ünü taşıyor, `run.replay_seed`
    ise state'i SIFIRDAN kurar (kendi şerhi: "silahlı plan varken çalıştırmak o planların
    altından zemini çeker")
  · düzeltmeden sonra kapanan işlemlerde öksüz YOK

AMA SUSTURMAK DA YANLIŞ OLURDU: aynı neden yeniden başlarsa (kırpma geri gelir, ya da
başka bir yol planı siler) satır sayısı ARTAR ve o an gerçek bir yazılım hatasıdır.
Bu yüzden kayıt bir TABAN taşır — cırcır: tabanın altı tarihsel, üstü NÜKS.
"""
from __future__ import annotations

from meridian import sieve


def _rapor(n_giren: int, n_cikan: int, drops: dict) -> dict:
    # `stages()` sözlüğün KENDİSİNİ aşama tablosu sayar (anahtar = aşama adı).
    return sieve.report({"llm_opinion_calibration.gercek":
                         {"in": n_giren, "out": n_cikan, "drops": drops}})


def _kural(r: dict, kural: str) -> list[dict]:
    return [v for v in r["violations"] if v["rule"] == kural]


def test_kapanmis_neden_YAZILIM_HATASI_demiyor():
    r = _rapor(893, 358, {"sema:plan_join_yok": 535})
    satir = _kural(r, "sema_elemesi")
    assert satir, "şema elemesi satırı KAYBOLMUŞ — susturma değil, DOĞRU CÜMLE isteniyordu"
    d = satir[0]["detail"]
    assert "yazılım hatasıdır" not in d, (
        "kapanmış bir neden hâlâ 'yazılım hatasıdır' diyor — operatör kapalı bir kusurun "
        f"peşine gönderiliyor: {d}")
    assert "2026-08-23" in d, "kapanış TARİHİ cümlede yok — okuyucu ne zaman kapandığını bilemez"
    assert "geri" in d.lower(), "kaybın geri gelmeyeceği söylenmiyor"


def test_TABAN_ASILIRSA_yeniden_yazilim_hatasi():
    """Nüks sessiz kalamaz: taban aşıldığında cümle eski sertliğine döner."""
    taban = sieve.KAPANMIS_SEMA["sema:plan_join_yok"]["taban"]
    r = _rapor(2000, 100, {"sema:plan_join_yok": taban + 1})
    d = _kural(r, "sema_elemesi")[0]["detail"]
    assert "yazılım hatasıdır" in d or "NÜKS" in d.upper(), (
        f"taban aşıldığı hâlde satır hâlâ tarihsel diyor — nüks görünmez oldu: {d}")


def test_KAPANMAMIS_neden_eski_cumleyi_KORUYOR():
    """Kayıtta olmayan bir şema nedeni hiçbir şey kaybetmemeli — kapı fazla kapsamamalı."""
    r = _rapor(100, 40, {"sema:bilinmeyen_alan": 60})
    d = _kural(r, "sema_elemesi")[0]["detail"]
    assert "yazılım hatasıdır" in d, f"kapanmamış neden yumuşatılmış: {d}"


def test_ORAN_satiri_kapanmis_nedende_sistematik_UYUMSUZLUK_demiyor():
    """Şiddet KRİTİK kalır (sonuç bugünün gerçeği) ama neden cümlesi düzelir.

    "%60 eksik kanıt" hükmü kapanmış nedende de geçerlidir — sebebin kapanması kanıtın
    geri geldiği anlamına gelmez. Değişen yalnız operatörün nereye bakacağı."""
    r = _rapor(893, 358, {"sema:plan_join_yok": 535})
    satir = _kural(r, "sema_orani_yuksek")
    assert satir, "oran satırı kaybolmuş — sonuç hâlâ gerçek, susturulamaz"
    assert satir[0]["severity"] == "kritik", "şiddet düşürülmüş — eksik kanıt hâlâ eksik kanıttır"
    d = satir[0]["detail"]
    assert "sistematik bir uyumsuzluk" not in d, f"kapanmış nedende hâlâ 'şu an bozuk' diyor: {d}"
    assert "eksik kanıtla hesaplanmıştır" in d, "asıl hüküm (sonuç) kaybolmuş"

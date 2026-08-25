"""HAVUZ ÖLÜ — TESLİMAT ÖLÇÜLMEYEN TEK MEKANİZMA · v313

VAKA (2026-08-25, operatör): "ajan en son 4 gün önce öneri sunmuş, öneri sayısı çok az gibi,
sadece 1 öneri ölçülmüş, hepsi de reddedilmiş — bir problem olabilir." Haklı çıktı.

ÖLÇÜLDÜ (canlı olay defteri):
    bg_reflection_start      son kayıt 2026-08-16, bugün 0
    hermes_search_start      son kayıt 2026-08-21, bugün 0
    hermes_proposal          son kayıt 2026-08-21, bugün 0
    arama_havuzu_zaman_asimi 2026-08-24: 9 · 2026-08-25: 8      ← BUGÜN ÖTÜYOR
Ve ataletin gövdesi: `probe_prefill biten=0 bekleyen=10` — havuz 10 iş gönderiyor, 1800 sn'de
HİÇBİRİ bitmiyor. "Yavaş" değil: tek bir iş bile tamamlanmıyor. Servis 17:31'de yeniden
başlatıldı (dağıtım), taze süreç aynısını üretiyor.

NEDEN KİMSE DUYMADI: `arama_havuzu_zaman_asimi` `obs.warn` ile yazılıyor ve `warn`ın kendi
şerhi diyor ki "alarm DEĞİLDİR: bildirim zincirini tetiklemez". 61 kayıt, günde 8-9, ve
operatörün gelen kutusuna HİÇ düşmedi.

BU ÇİVİNİN ASIL SEBEBİ — KENDİ DÜZELTMEM BU SESSİZLİĞİ DERİNLEŞTİRİYORDU:
v302 öncesi havuz ölünce nabız atılmıyordu → `MECHANISM_STALE hermes_poll` ötüyordu. Yanıltıcı
bir sinyaldi (mekanizma ölü değil MEŞGULdü) ama KAZARA bu arızanın tek sesiydi. v302 nabzı
bekleyişin içinden attırıyor, yani o alarmı SUSTURUYOR. Doğru düzeltme sinyali susturmak değil,
YANLIŞ sinyali DOĞRUSUYLA değiştirmektir: "iplik canlı" (v302, doğru) + "havuz hiçbir iş
bitirmiyor" (bu çivi, doğru). İkisi AYRI olgudur ve ikisi de söylenmelidir.

KAPSAM DAR: bu çivi havuzun NEDEN öldüğünü ölçmez — onu duyurur. Kök neden ayrı bir iştir.
"""
from __future__ import annotations

import inspect

from meridian import obs, reflect


def test_ALARM_jetonu_VAR():
    """Teslimat arızasının kendi jetonu olmalı — `warn` bildirim zincirini tetiklemez."""
    assert hasattr(obs, "ALARM_ARAMA_HAVUZU_OLU"), (
        "havuz ölümü için ALARM jetonu YOK — olay `warn` olarak kalırsa operatöre HİÇ ulaşmaz "
        "(obs.warn şerhi: 'alarm DEĞİLDİR: bildirim zincirini tetiklemez')")
    assert isinstance(obs.ALARM_ARAMA_HAVUZU_OLU, str) and obs.ALARM_ARAMA_HAVUZU_OLU


def test_jeton_bildirim_kapsaminda():
    """NOTIFY_TOKENS bir EL LİSTESİ değil TÜRETMEdir (obs.py başlığı) — yeni jeton
    kendiliğinden kapsama girmeli. Girmiyorsa türetme bozulmuş demektir."""
    jetonlar = getattr(obs, "NOTIFY_TOKENS", None)
    assert jetonlar is not None, "NOTIFY_TOKENS yok — bildirim kapsamı ölçülemiyor"
    assert obs.ALARM_ARAMA_HAVUZU_OLU in jetonlar, (
        f"yeni jeton bildirim kapsamında DEĞİL — türetme el listesine dönmüş: {sorted(jetonlar)}")


def test_atalet_ALARM_basiyor_warn_DEGIL():
    """ASIL ÇİVİ: `_HavuzAtaleti` yükselten yol artık ALARM basmalı. `warn` yetmez."""
    src = inspect.getsource(reflect)
    assert "ALARM_ARAMA_HAVUZU_OLU" in src, (
        "havuz atalet yolu hâlâ yalnız `warn` yazıyor — bildirim zinciri tetiklenmez, "
        "operatör 4 gün boyunca hiçbir şey duymaz (2026-08-21→08-25 vakası)")


def _alarm_cagrilari() -> list[str]:
    """Her `_obs.alarm(_obs.ALARM_ARAMA_HAVUZU_OLU …)` çağrısının ARGÜMAN BLOĞUNU döndürür.

    NEDEN BLOK BAZINDA: düz `"biten" in src` iki mutasyonu birden kaçırdı — o dize komşu
    `warn` satırında da geçiyor ve ilk çağrıda durduğu için İKİNCİ çağrı boşaltılabiliyordu.
    Alt-dize tuzağı; her çağrı AYRI AYRI sınanır."""
    src = inspect.getsource(reflect)
    bloklar, ara = [], "_obs.alarm(_obs.ALARM_ARAMA_HAVUZU_OLU"
    i = src.find(ara)
    while i != -1:
        derinlik, j = 0, src.index("(", i + len("_obs.alarm") - 1)
        for k in range(j, len(src)):
            if src[k] == "(":
                derinlik += 1
            elif src[k] == ")":
                derinlik -= 1
                if derinlik == 0:
                    bloklar.append(src[j:k + 1])
                    break
        i = src.find(ara, i + 1)
    return bloklar


def test_HER_alarm_cagrisi_SAYIYI_tasiyor():
    """UYDURMA YASAĞI komşusu: alarm 'havuz öldü' demekle kalmamalı, KAÇ iş bitti / kaç
    bekliyor / kaç saniye beklendi taşımalı. 'biten=0, bekleyen=10' teşhisin kendisiydi."""
    bloklar = _alarm_cagrilari()
    assert len(bloklar) >= 2, (
        f"iki havuzun ikisi de alarm basmalı (probe_prefill + incumbent_prefill), "
        f"bulunan: {len(bloklar)}")
    for b in bloklar:
        for alan in ("biten=", "bekleyen=", "atalet_sn="):
            assert alan in b, (
                f"bir alarm çağrısı '{alan}' taşımıyor — sayısız alarm teşhis edilemez:\n{b[:200]}")


def test_HER_alarm_cagrisi_HAVUZ_KIMLIGI_tasiyor():
    """İki ayrı havuz var (incumbent_prefill / probe_prefill) ve hangisinin öldüğü teşhisin
    yarısıdır — canlıda ölen `probe_prefill`di. Kimlik ALARMIN KENDİSİNDE olmalı; komşu
    `warn` satırında geçmesi kanıt DEĞİLDİR."""
    yerler = set()
    for b in _alarm_cagrilari():
        assert "yer=" in b, f"alarm çağrısı havuz kimliği taşımıyor:\n{b[:200]}"
        for ad in ("probe_prefill", "incumbent_prefill"):
            if f'yer="{ad}"' in b:
                yerler.add(ad)
    assert yerler == {"probe_prefill", "incumbent_prefill"}, (
        f"iki havuzun ikisi de kendi kimliğiyle alarm basmalı, bulunan: {sorted(yerler)}")


def test_warn_kaydi_SILINMEDI():
    """Aşırıya kaçma çivisi: alarm EKLENİR, mevcut `warn` kaydı KALDIRILMAZ. Olay defterinin
    tarihçesi (61 kayıt) aynı adla sürmeli, yoksa geçmişle kıyas kopar."""
    src = inspect.getsource(reflect)
    # HAM SAYIM YETMEZ (mutasyonla yakalandı): ad yorumda da geçiyor, bir çağrı yeniden
    # adlandırılınca sayı hâlâ eşiği geçiyordu. İKİ `warn` ÇAĞRISI da ayrı ayrı aranır.
    for yer in ("probe_prefill", "incumbent_prefill"):
        assert f'_obs.warn("arama_havuzu_zaman_asimi", yer="{yer}"' in src, (
            f"{yer} havuzunun tarihsel `warn` kaydı yeniden adlandırılmış/silinmiş — "
            "olay defterindeki 61 kayıtlık seriyle kıyas kopar")

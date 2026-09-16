"""test_coherence_kadans_v505.py — TSK-191: türev bayatlık eşiği ÜRETİCİ KADANSINDAN türer.

ÖLÇÜLEN ARIZA (A1, 2026-09-15 20:43Z): `watchdog.coherence_report` her türev artefakt için
kaynaklarının en yeni damgasına göre `behind_h` hesaplıyor ve SABİT bir payı (1 saat, "bir sonraki
döngü zaten tazeler") aşan her türevi `stale` sayıyordu. Pay günlük kadanslı türevler için
doğrudur; HAFTALIK yazılan iki türev için değildir:

  · `arming_report.json`  — üretici mekanizma `arming_eval` (scheduler haftalık kadansı, nabız
    penceresi `EXPECTED["arming_eval"]` = 9 gün)
  · `self_review.json`    — üretici `selfreview.weekly` (haftalık; nabız ATMIYOR, bu yüzden
    `EXPECTED`te kaydı YOK — eşiği kaydın kendisinde açık `kadans_s` olarak yazılıdır)

İkisi de kaynak defterleri (cf/trades) her gün ilerlediği için HER GÜN "24 sa geride" diye
`MECHANISM_STALE BAYAT TÜREV` üretiyordu — Ağustos'tan beri ~23 olay. BEDEL YASASI'nın tersi:
alarm üretiliyor ama BİLGİ taşımıyor; operatör onu görmezden gelmeyi öğrenir ve aynı jeton GERÇEK
bir bayatlıkta da sessiz kalır.

TEK KAYNAK: eşik iki yerde duruyordu (mekanizma kadansı `EXPECTED`te, tolerans
`COHERENCE_GRACE_S`te) ve ikisi BİRBİRİNİ HİÇ GÖRMÜYORDU. Bu dosya bağı çivilir:
izin verilen gecikme = üretici kadansı + pay.

BEŞ ÇİVİ:
  (a) haftalık türev kadansının İÇİNDE geride (6 gün) → bayat DEĞİL
  (b) haftalık türev kadansı AŞMIŞ (10 gün) → bayat; `behind_h` ve `esik_h` dolu
  (c) mekanizması kayıtlı OLMAYAN günlük türev 2 sa geride → bayat (eski davranış KORUNUR)
  (d) kayıttaki her mekanizma adı `EXPECTED`te var ya da açık `kadans_s` taşır (ayrışma çivisi)
  (e) alarm metni + alan eşiği TAŞIR — okuyucusuz sayı yazılmaz (Yasa 6)
"""
from __future__ import annotations

import os
import time

import pytest

from meridian import config, watchdog


# --------------------------------------------------------------------------------------------
# yardımcı: türev `geri_s` saniye önce, kaynaklarının HEPSİ şimdi damgalanır
# --------------------------------------------------------------------------------------------
def _damgala(art: str, geri_s: float) -> None:
    """`art` türevini ve BEYAN EDİLMİŞ kaynaklarını sandbox state'e yazıp damgalar.

    Kaynaklar `watchdog.DERIVED_SOURCES`ten okunur (test kendi kopyasını TUTMAZ — kopya sessizce
    ayrışırdı). Türevin damgası kaynaktan `geri_s` saniye geride durur. TSK-203: kaynak ve türev
    damgaları BİRLİKTE `COHERENCE_GRACE_S` + 60 sn geçmişe alınır — az önce yazılmış kaynak sıra
    yarışıdır ve bayrak kaldırmaz; aradaki `geri_s` farkı ve çivilerin iddiaları korunur."""
    t = time.time() - watchdog.COHERENCE_GRACE_S - 60   # TSK-203: kaynak damgası grace'in ötesine alındı, yarış tanımı
    yol = config.STATE / art
    yol.write_text("{}")
    for src in watchdog.DERIVED_SOURCES[art]:
        s = config.STATE / src
        s.write_text('{"id": "x"}\n' if src.endswith(".jsonl") else "{}")
        os.utime(s, (t, t))
    os.utime(yol, (t - geri_s, t - geri_s))


def _bayat_mi(art: str) -> dict | None:
    """`art` için `coherence_report` satırı (yoksa None) — hükmü tek yerden okuruz."""
    for s in watchdog.coherence_report()["stale"]:
        if s["artifact"] == art:
            return s
    return None


# `DERIVED_MECHANISM` kaydındaki HAFTALIK türevler; eşikleri kaynağından türetilir, test sabit
# saymaz (sabit sayı ikinci bir kaynak olurdu — tam da bu turun kapattığı kusur).
HAFTALIK = ("arming_report.json", "self_review.json")


# --------------------------------------------------------------------------------------------
# (a) KADANSIN İÇİNDE — BAYAT DEĞİL
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("art", HAFTALIK)
def test_a_haftalik_turev_6_gun_geride_BAYAT_DEGIL(sandbox_state, art):
    """Haftalık yazılan bir türev, kaynağı her gün ilerlerken 6 gün geride olabilir ve bu NORMAL
    çalışmadır. Eski sabit pay (1 sa) burada her gün alarm üretiyordu."""
    _damgala(art, 6 * 24 * 3600)
    assert _bayat_mi(art) is None, \
        f"{art} kadansının İÇİNDE (6 gün) bayat sayıldı — sahte alarm sınıfı geri geldi"


# --------------------------------------------------------------------------------------------
# (b) KADANSI AŞMIŞ — BAYAT, İKİ SAYI DA DOLU
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("art", HAFTALIK)
def test_b_haftalik_turev_10_gun_geride_BAYAT(sandbox_state, art):
    """Gevşetme körlük DEĞİLDİR: kadans + pay aşılınca hüküm yine `stale`dir ve rapor İKİ sayıyı
    da taşır — `behind_h` (ne kadar geride) ve `esik_h` (ne kadarına izin var)."""
    _damgala(art, 10 * 24 * 3600)
    s = _bayat_mi(art)
    assert s is not None, f"{art} 10 gün geride ve bayat SAYILMADI — dedektör kör kaldı"
    assert s["behind_h"] == pytest.approx(240.0, abs=1.0)
    esik_s = watchdog._coherence_esik_s(art)
    assert s["esik_h"] == pytest.approx(esik_s / 3600, abs=0.01)
    assert s["esik_h"] > 24, "haftalık türevin eşiği bir günden dar — kadans bağı kopmuş"


# --------------------------------------------------------------------------------------------
# (c) MEKANİZMASIZ TÜREV — ESKİ DAVRANIŞ KORUNUR
# --------------------------------------------------------------------------------------------
def test_c_mekanizmasiz_gunluk_turev_2_sa_geride_BAYAT(sandbox_state):
    """Kayıtta mekanizması OLMAYAN türev eski dar payla ölçülür (döngü kadansı, 1 sa). Gevşetme
    yalnız BEYAN EDİLMİŞ kadanslar içindir; beyansız türev için hiçbir şey değişmez."""
    assert "near_miss.json" not in watchdog.DERIVED_MECHANISM
    _damgala("near_miss.json", 2 * 3600)
    s = _bayat_mi("near_miss.json")
    assert s is not None, "mekanizmasız türevin eski (dar) eşiği gevşetildi — dedektör körleşti"
    assert s["esik_h"] == pytest.approx(watchdog.COHERENCE_GRACE_S / 3600, abs=0.01)


# --------------------------------------------------------------------------------------------
# (d) AYRIŞMA ÇİVİSİ — KAYIT ↔ EXPECTED
# --------------------------------------------------------------------------------------------
def test_d_kayittaki_her_mekanizma_EXPECTED_te_ya_da_acik_kadansli():
    """TEK KAYNAK: eşik `EXPECTED`ten türer. Kaydedilmiş bir mekanizma adı `EXPECTED`te yoksa ve
    açık `kadans_s` de taşımıyorsa, eşik sessizce eski dar paya düşer — yani düzeltme ölür ve
    kimse görmez. Bu çivi o sessizliği kırar."""
    for art, kayit in watchdog.DERIVED_MECHANISM.items():
        mek = kayit.get("mekanizma")
        assert mek, f"{art} kaydı mekanizma adı taşımıyor"
        kadans = kayit.get("kadans_s")
        assert mek in watchdog.EXPECTED or isinstance(kadans, (int, float)), \
            (f"{art} → mekanizma `{mek}` EXPECTED'te YOK ve açık `kadans_s` de yok: eşik "
             f"sessizce 1 sa'ya düşer (ayrışma)")
        if kadans is not None:
            assert kadans > 0, f"{art} açık kadansı pozitif değil"


def test_d2_kayitli_her_turev_DERIVED_SOURCES_te_var():
    """Kaydı olan ama kaynağı beyan edilmemiş türev ÖLÜ bir satırdır: `coherence_report` onu hiç
    görmez, yani kadans beyanı hiçbir hükme girmez (Yasa 6'nın kayıt tarafı)."""
    yetim = set(watchdog.DERIVED_MECHANISM) - set(watchdog.DERIVED_SOURCES)
    assert not yetim, f"kaynağı beyan edilmemiş kadans kaydı: {yetim}"


# --------------------------------------------------------------------------------------------
# (e) ALARM EŞİĞİ TAŞIR
# --------------------------------------------------------------------------------------------
def test_e_bayat_turev_alarmi_ESIGI_tasir(sandbox_state, monkeypatch):
    """`esik_h` OKUYUCUSUZ YAZILMAZ (Yasa 6): operatörün gördüğü satır "N sa geride" derken
    "eşik neydi" sorusunu cevaplamıyordu — 217 sa eşikli bir türevin 240 sa geride olması ile
    1 sa eşikli birinin 2 sa geride olması AYNI cümleyle anlatılamaz."""
    from meridian import obs

    yakalanan: list[tuple] = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **f: yakalanan.append((tok, msg, f)))

    rep = {ad: dict(v) for ad, v in watchdog._DEDEKTOR_BOS.items()}
    rep["determinism"] = {"ok": True}
    rep["coherence"] = {"stale": [{"artifact": "arming_report.json",
                                   "behind_h": 240.0, "esik_h": 217.0}],
                        "ok": 0, "absent": [], "total": 1}
    monkeypatch.setattr(watchdog, "integrity_report", lambda persist=False: rep)
    watchdog.check_integrity_and_alarm()

    satir = [(t, m, f) for t, m, f in yakalanan if f.get("kind") == "coherence"]
    assert satir, "BAYAT TÜREV alarmı hiç üretilmedi"
    _tok, mesaj, alanlar = satir[0]
    assert "217" in mesaj, f"alarm metni eşiği taşımıyor: {mesaj}"
    assert alanlar.get("esik_h") == 217.0, "alarm `esik_h` ALANINI basmıyor — sayı ayrıştırılamaz"
    assert alanlar.get("behind_h") == 240.0, "TSK-102 tüketicisi `behind_h` kayboldu"

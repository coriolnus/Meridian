"""BRİFİNG KADANSI: hesaplanan teslim edilir, boşken SESSİZ — v327 (2026-08-27)

ÖLÇÜM (2026-08-27, canlı A1):
    notify_undelivered.json   toplam 310 · MECHANISM_STALE 208 · MIRROR_DRIFT 51 · NAKED_POSITION 9
    ops/alarm_backlog_digest.py  YAZILMIŞ, çalışıyor, ama HİÇBİR KADANSA ASILI DEĞİL
    improvement_proposals.jsonl  16 öneri, teslimat yolu YOK

Yani sistem hesaplıyor ve kimse okumuyor — bu deponun ölçülmüş hastalığı (`candidate_review.json`
günde 23 bin karakter üretiyor ve karar hattında okuyucusu yok).

SESSİZLİK ŞARTI PAZARLIĞA KAPALI: karar döndürmeyen zamanlanmış iş bildirim spam'idir. Yeni
bir şey yoksa mesaj YOKTUR.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/oneri_brifingi.py"
SERVICE = KOK / "deploy/oracle-a1/meridian-brifing.service"
TIMER = KOK / "deploy/oracle-a1/meridian-brifing.timer"


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    spec = importlib.util.spec_from_file_location("oneri_brifingi", BETIK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_BOSKEN_SESSIZ(monkeypatch, sandbox_state):
    """Okunmamış öneri yoksa mesaj ÜRETİLMEZ. Karar döndürmeyen bildirim spam'dir."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [])
    o = mod.ozet_kur()
    assert o["yeni"] == 0
    assert not o["mesaj"], f"boş defterde mesaj üretildi: {o['mesaj']!r}"


def test_YENI_ONERI_MESAJA_GIRER(monkeypatch, sandbox_state):
    """Okunmamış öneri varsa mesajda kimliği ve alanı geçer."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "coverage_ariza.hotstate",
         "oneri": "watchdog hotstate sayacını harici süreçten okunur yap", "oncelik": "yuksek"},
    ])
    o = mod.ozet_kur()
    assert o["yeni"] == 1
    assert "N00017" in o["mesaj"] and "coverage_ariza.hotstate" in o["mesaj"]


def test_TESLIMDEN_SONRA_TEKRARLAMAZ(monkeypatch, sandbox_state):
    """Damga basıldıktan sonra aynı öneri ikinci kez bildirilmez."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00017", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main(["--uygula"]) == 0
    assert len(gonderilen) == 1
    assert mod.ozet_kur()["yeni"] == 0, "damga basılmamış — aynı öneri yeniden bildirilir"


def test_KURU_KOSUM_VARSAYILAN(monkeypatch, sandbox_state):
    """`--uygula` olmadan HİÇBİR ŞEY gönderilmez ve damga basılmaz."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00018", "alan": "x", "oneri": "y"},
    ])
    gonderilen = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    assert mod.main([]) == 0
    assert not gonderilen, "kuru koşumda gönderdi"
    assert mod.ozet_kur()["yeni"] == 1, "kuru koşumda damga bastı"


def test_BIRIM_ALARM_DIGESTINI_DE_KOSUYOR():
    """Kadans iki teslimatı da tetiklemeli; biri unutulursa 310'luk yığın orada kalır."""
    assert SERVICE.exists() and TIMER.exists(), "systemd birimleri yok"
    s = SERVICE.read_text(encoding="utf-8")
    assert "alarm_backlog_digest.py" in s and "--uygula" in s, "alarm yığını koşulmuyor"
    assert "oneri_brifingi.py" in s, "öneri brifingi koşulmuyor"


def test_TIMER_GUNLUK():
    t = TIMER.read_text(encoding="utf-8")
    assert "OnCalendar=" in t, "timer takvim tanımı yok"
    assert "Persistent=true" in t, (
        "Persistent yok — makine kapalıyken kaçan tetik telafi edilmez")


def test_dagit_F9_birimleri_IZLIYOR():
    metin = (KOK / "dagit.sh").read_text(encoding="utf-8")
    for ad in ("meridian-brifing.service", "meridian-brifing.timer"):
        assert f"deploy/oracle-a1/{ad}|/etc/systemd/system/{ad}" in metin, f"F9 {ad}'i izlemiyor"


# ---- DÜZELTME TURU 1 (2026-08-29 denetimi) — iki çivi, ikisi de "öneri KALICI kaybolabilir" ----

def test_TS_SIZ_SATIR_SESSIZCE_DUSMEZ(monkeypatch, sandbox_state):
    """ts alanı olmayan/boş bir öneri sessizce dışlanamaz: `"" > ""` her zaman False olduğu için
    eski kod böyle bir satırı NE İLK TURDA NE DE HİÇBİR ZAMAN bildirmiyordu — `toplam`a sayılmaya
    devam ederken mesajda hiç görünmüyordu (kalıcı sessiz dışlama). Düzeltme: ts'siz satır
    KOŞULSUZ `yeni`ye girer ve mesajda ölçülemediği açıkça işaretlenir (UYDURMA YASAĞI: eksik
    alan gizlenmez, beyan edilir; ts UYDURULMAZ)."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"id": "N00099", "alan": "ts_eksik.alani", "oneri": "ts alanı olmadan üretilmiş satır"},
    ])
    o = mod.ozet_kur()
    assert o["yeni"] == 1, f"ts'siz satır sessizce düşürüldü: {o}"
    assert "N00099" in o["mesaj"] and "ts_eksik.alani" in o["mesaj"]


def test_GONDERIM_PENCERESINDE_EKLENEN_SATIR_KACIRILMAZ(monkeypatch, sandbox_state):
    """Gönderim SIRASINDA (network POST penceresinde) deftere düşen bir satır, mesaj zaten
    KURULDUKTAN sonra geldiği için o turun mesajında YOKTUR. Eski kod damgayı `notify.send`
    DÖNDÜKTEN SONRA yapılan İKİNCİ bir okumadan hesaplıyordu — bu ikinci okuma pencere
    içinde eklenen satırı da görüyor ve damga onu "gördüm" sayıyordu, hiç bildirmemiş olarak.
    Düzeltme: damga yalnız GÖNDERİLEN mesajı üreten enstantaneden ilerler; gönderim sonrası
    ikinci bir defter okuması YOK."""
    mod = _yukle()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": "2026-08-27T10:00:00+00:00", "id": "N00020", "alan": "x", "oneri": "ilk satır"},
    ])

    def _sahte_gonder(text):
        # notify.send'in GERÇEK ağ çağrısı sırasında BAŞKA bir yazar (nous_eval.py gibi) deftere
        # yeni bir satır ekliyor — bu satır gönderilen `text`te YOKTUR.
        store.write_jsonl("improvement_proposals.jsonl", [
            {"ts": "2026-08-27T10:00:00+00:00", "id": "N00020", "alan": "x", "oneri": "ilk satır"},
            {"ts": "2026-08-27T10:05:00+00:00", "id": "N00021", "alan": "y",
             "oneri": "gönderim sırasında eklendi"},
        ])
        return True

    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", _sahte_gonder)
    assert mod.main(["--uygula"]) == 0

    o2 = mod.ozet_kur()
    assert o2["yeni"] == 1, (
        f"gönderim penceresinde eklenen satır bir sonraki turda KAÇIRILDI: {o2}")
    assert "N00021" in o2["mesaj"]

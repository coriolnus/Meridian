"""v414 — TSK-131 ALT-İŞ: A1 /opt/veri DİSK EŞİĞİ BEKÇİSİ (2026-09-05).

ÖLÇÜLEN BOŞLUK (D1, bu turun ölçümü): `grep -rn "disk_usage|statvfs|/opt/veri|df " meridian/
watchdog.py meridian/*.py ops/bekci_tarama.py ops/bekci_brifingi.py deploy/oracle-a1/
geridolum.py` tek isabeti `geridolum.py::_bos_disk_bayt` idi — geri dolumun KENDİ iş-açma kapısı
(ham-geçici alan <25 G kalınca dur). Hiçbir sensör /opt/veri'nin TOPLAM kullanımını izleyip
OPERATÖRE önceden haber vermiyordu. Operatör kararı (ROADMAP TSK-131, 2026-09-05): geri dolum
DEVAM, 120 G tavanında (`deploy/oracle-a1/geridolum.py::TAVAN_BAYT` — TEK KAYNAK) ele alınır; bu
bekçi o karardan 10 G ÖNCE (110 G) haber verir.

SÖZLEŞME (bu dosya çiviler):
  * `watchdog.veri_disk_report()` → {var, kullanilan_g, toplam_g, bos_g, esik_g, esik_asildi,
    olculemedi_neden}: yol yoksa (yerel makine/CI — A1 dışında gerçek bir yokluk) `var=False` +
    `olculemedi_neden`, `esik_asildi=False` HER ZAMAN — ölçülemeyen eşik aşılmış SAYILMAZ
    (UYDURMA YASAĞI).
  * `watchdog.check_veri_disk_and_alarm()` — eşik aşımı başına günde EN ÇOK
    `GUNLUK_ALARM_TAVANI` (=1) kez `DISK_ESIK` alarmı; günlük tavan MECHANISM_STALE ile AYNI
    defteri (`ALARM_GUNLUK_FILE`) paylaşır (tek kaynak — yeni dosya açılmadı). Yol yok/
    ölçülemedi ya da eşik altı → alarm YOK.
  * YASA 6 okuyucu: `check_and_alarm()` bu bekçiyi KENDİ try'ında çağırır (AST çivisi — metin
    çapası DEĞİL, watchdog.py motor dosyası `dosya.py:NNN` sıfır toleransı v382).
"""
from __future__ import annotations

import ast
import pathlib
import types

import pytest

from meridian import store, watchdog

SRC = pathlib.Path(__file__).resolve().parents[1]

G = 1_000_000_000  # geridolum.py::TAVAN_BAYT ile AYNI birim sözleşmesi — GB, GiB değil


def _kullanim(kullanilan_g: float, toplam_g: float) -> types.SimpleNamespace:
    """Sahte `shutil.disk_usage` dönüşü — yalnız `total`/`free` erişilir (kod `used`e bakmaz)."""
    toplam = int(toplam_g * G)
    bos = int((toplam_g - kullanilan_g) * G)
    return types.SimpleNamespace(total=toplam, used=toplam - bos, free=bos)


@pytest.fixture
def alarmlar(monkeypatch):
    """obs.alarm çağrılarını yakalar — bekçi felsefesi gereği tek gözlenebilir çıktı budur
    (eod_supurme/koruma bekçilerinin test fikstürüyle AYNI desen)."""
    from meridian import obs
    kayit: list[dict] = []

    def _yakala(token, message, **fields):
        kayit.append({"token": token, "message": message, **fields})
        return {"token": token}

    monkeypatch.setattr(obs, "alarm", _yakala)
    return kayit


@pytest.fixture
def diskli(sandbox_state, monkeypatch, tmp_path):
    """`/opt/veri` VAR gibi davranan sandbox: yol gerçekten var olan bir tmp dizine bağlanır,
    `shutil.disk_usage` sahte değer döner. Zaman çivilenir ki 'aynı gün' ölçülebilsin."""
    yol = tmp_path / "opt_veri"
    yol.mkdir()
    monkeypatch.setattr(watchdog, "VERI_DISK_YOLU", str(yol))
    monkeypatch.setattr(watchdog, "_now", lambda: 1_800_000_000.0)  # sabit gün (UTC)
    return yol


def _kullanimi_ayarla(monkeypatch, kullanilan_g: float, toplam_g: float = 147.0) -> None:
    monkeypatch.setattr(watchdog.shutil, "disk_usage",
                         lambda _yol: _kullanim(kullanilan_g, toplam_g))


# ---- (1) eşik aşıldı → BİR alarm ------------------------------------------------------------

def test_esik_asildi_bir_alarm(diskli, alarmlar, monkeypatch):
    _kullanimi_ayarla(monkeypatch, 111.0)
    rep = watchdog.check_veri_disk_and_alarm()
    assert rep["var"] is True
    assert rep["kullanilan_g"] == 111.0
    assert rep["esik_asildi"] is True
    assert len(alarmlar) == 1
    assert alarmlar[0]["token"] == "DISK_ESIK"
    assert alarmlar[0]["kullanilan_g"] == 111.0
    assert alarmlar[0]["esik_g"] == watchdog.VERI_DISK_ESIK_G


# ---- (2) eşik altı → alarm yok -------------------------------------------------------------

def test_esik_altinda_alarm_yok(diskli, alarmlar, monkeypatch):
    _kullanimi_ayarla(monkeypatch, 100.0)
    rep = watchdog.check_veri_disk_and_alarm()
    assert rep["var"] is True
    assert rep["kullanilan_g"] == 100.0
    assert rep["esik_asildi"] is False
    assert alarmlar == []


# ---- (3) yol yok → None + neden, alarm yok --------------------------------------------------

def test_yol_yok_none_ve_neden(sandbox_state, alarmlar, monkeypatch, tmp_path):
    monkeypatch.setattr(watchdog, "VERI_DISK_YOLU", str(tmp_path / "yok_boyle_bir_yer"))
    rep = watchdog.veri_disk_report()
    assert rep["var"] is False
    assert rep["kullanilan_g"] is None
    assert rep["toplam_g"] is None
    assert rep["bos_g"] is None
    assert rep["esik_asildi"] is False
    assert rep["olculemedi_neden"]                     # UYDURMA YASAĞI: None yerine gerekçe
    assert "yok" in rep["olculemedi_neden"]
    assert watchdog.check_veri_disk_and_alarm() == rep
    assert alarmlar == []


# ---- (4) aynı gün ikinci çağrı → mandal (tekrar yok) ----------------------------------------

def test_ayni_gun_ikinci_cagri_mandallanir(diskli, alarmlar, monkeypatch):
    _kullanimi_ayarla(monkeypatch, 111.0)
    watchdog.check_veri_disk_and_alarm()
    watchdog.check_veri_disk_and_alarm()               # AYNI gün, AYNI eşik aşımı — tekrar YOK
    assert len(alarmlar) == 1, "günlük tavan aşıldı: ikinci çağrı yeni satır ÜRETMEMELİ (mandal)"
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    satir = doc["mekanizmalar"][watchdog._VERI_DISK_MEK_ADI]
    assert satir["alarm"] == 1
    assert satir["bastirilan"] == 1, "bastırılan SESSİZ DEĞİL — sayaçta GÖRÜNÜR olmalı (YASA 6)"


# ---- YASA 6: okuyucu zinciri (AST çivisi — metin çivisi değil) ------------------------------

def test_zincir_check_and_alarm_kendi_tryinda_cagirir():
    agac = ast.parse((SRC / "meridian" / "watchdog.py").read_text(encoding="utf-8"))
    fn = next(n for n in agac.body
              if isinstance(n, ast.FunctionDef) and n.name == "check_and_alarm")
    hedefli_try = None
    for tr in (n for n in ast.walk(fn) if isinstance(n, ast.Try)):
        adlar = {c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", None)
                 for c in ast.walk(tr) if isinstance(c, ast.Call)
                 if isinstance(c.func, (ast.Name, ast.Attribute))}
        if "check_veri_disk_and_alarm" in adlar:
            hedefli_try = tr
            break
    assert hedefli_try is not None, (
        "check_and_alarm zinciri check_veri_disk_and_alarm'ı çağırmıyor — sensör OKUYUCUSUZ "
        "(YASA 6): bekçi yazılmış ama zincire bağlanmamış")
    # yalıtım: kendi try'ı Exception yakalar (akranlarının deseni — biri düşünce zincir düşmez)
    assert any(isinstance(h.type, ast.Name) and h.type.id == "Exception"
               for h in hedefli_try.handlers)


# ---- jeton NOTIFY_TOKENS'a kendiliğinden girer (obs.py ALARM_ türetmesi) --------------------

def test_disk_esik_jetonu_notify_tokens_icinde():
    from meridian import obs
    assert obs.ALARM_DISK_ESIK == "DISK_ESIK"
    assert obs.ALARM_DISK_ESIK in obs.NOTIFY_TOKENS

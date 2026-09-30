"""v605 — TSK-259: DISK_ESIK alarmı İLERİ DOLDURMA İŞİ KOŞARKEN ölçmez (operatör 2026-09-30 18:5xZ).

VAKA (Rol-1 A1 ölçümü, 2026-09-30): `DISK_ESIK` 09-25 07:36Z · 09-26 21:39Z · 09-29 08:41Z · 09-30 07:38Z
öttü — DÖRDÜ de `meridian-geridolum.service` koşumlarının İÇİNDE (koşum ~25–32 dk; journal "TAVAN aşıldı:
yalnız ileri günler dolduruluyor"). Kalıcı kullanım `df` ile ≈122 GB (%82); alarm anlarında 142–144 GB —
fark işin geçici ham/işleme alanıdır ve iş kendini zaten korur (`geridolum.py::ILERI_DISK_PAYI_BAYT`,
`geridolum.py::bos_bayt`). Alarm neredeyse HER GÜN ötüyordu: gerçek dolmayı gizleyen körleşme sınıfı.

OPERATÖR KARARI: "iş koşarken ölçme" — alarm yalnız KALICI doluluğu eşikler; eşik
`watchdog.VERI_DISK_ESIK_G` = 140 AYNI kalır (operatör 2026-09-12).

SÖZLEŞME (bu dosya çiviler):
  1. iş koşuyor + eşik aşıldı → alarm YOK; atlama GÖRÜNÜR (`veri_disk_esigi` satırında
     `atlandi_is_kosuyor` sayacı + `atlanan_tepe_g`; okuyucu `api._alarm_gunluk()` — YASA 6).
  2. iş koşmuyor + eşik aşıldı → bugünkü davranış AYNEN (günlük tavan + `DISK_ESIK`).
  3. TAKILI İŞ KÖRLÜK YARATMAZ: iş `watchdog.TASMA_SN`den uzun koşuyorsa ölçüm yapılır, alarm normal
     kurallarla çalar, mesaj "iş X dk'dır koşuyor" der.
  4. iş durumu ÖLÇÜLEMEDİ (yol yok / izin yok / beklenmedik biçim) → "koşmuyor" SAYILIR (güvenli yön:
     alarm çalar); neden alarm gövdesinde.
  5. `/opt/veri` yok (yerel/CI) → bugünkü "ölçülemedi, alarm yok"; süreç tablosu HİÇ okunmaz.
TESPİT YÖNTEMİ (a) — `/proc` taraması (`watchdog.geridolum_is_durumu`): alt süreç açmaz, işin flock
kilidine dokunmaz. Öncülü birim sertleştirmesidir (iki birim aynı kullanıcı, meridian.service'te
PrivatePIDs/ProcSubset/ProtectProc/PrivateUsers YOK) — öncül burada çivilenir, sertleştirme turu onu
bozarsa çivi öter. GERÇEK `/proc` OKUNMAZ: her test sahte bir süreç tablosu kurar.
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import types

import pytest

from meridian import store, watchdog
from tests.test_veri_disk_esigi_v414 import alarmlar  # noqa: F401 — fikstür ithali pytest'e görünürlük içindir

SRC = pathlib.Path(__file__).resolve().parents[1]
BIRIM_KOK = SRC / "deploy" / "oracle-a1"

G = 1_000_000_000          # geridolum.py::TAVAN_BAYT ile AYNI birim sözleşmesi — GB, GiB değil
TCK = 100                  # sahte SC_CLK_TCK
UPTIME_SN = 100_000.0      # sahte makine çalışma süresi

SURUCU_ARGV = ["/opt/veri/pilot-venv/bin/python", "/opt/veri/geridolum.py"]
UVICORN_ARGV = ["/home/ubuntu/.local/bin/uv", "run", "uvicorn", "meridian.api:app"]


# ---- sahte süreç tablosu ---------------------------------------------------------------------

def _stat_satiri(pid: int, starttime_tik: int, comm: str = "python") -> str:
    """`/proc/<pid>/stat` biçimi: `pid (comm) durum ppid … alan22=starttime …`. Alanlar 3..21
    sıradan doldurulur, 22. alan başlangıç tikidir (makine açılışından beri)."""
    ara = ["S"] + ["0"] * 18                   # alan 3 (durum) + alan 4..21
    return f"{pid} ({comm}) " + " ".join(ara + [str(starttime_tik), "0", "0"]) + "\n"


def _surec(kok: pathlib.Path, pid: int, argv: list[str], yas_sn: float | None = None,
           comm: str = "python", stat: str | None = None) -> None:
    d = kok / str(pid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
    if stat is not None:
        (d / "stat").write_text(stat)
    elif yas_sn is not None:
        (d / "stat").write_text(_stat_satiri(pid, int((UPTIME_SN - yas_sn) * TCK), comm))


@pytest.fixture
def proc(monkeypatch, tmp_path):
    """Sahte `/proc` kökü: `uptime` + bir uvicorn süreci (kendi sürecimizin ikizi). Testler
    üstüne `_surec` ile ekler. `SC_CLK_TCK` sabitlenir."""
    kok = tmp_path / "proc"
    kok.mkdir()
    (kok / "uptime").write_text(f"{UPTIME_SN:.2f} 123456.78\n")
    for ad in ("self", "stat", "meminfo"):                 # sayısal olmayan girdiler süreç değildir
        (kok / ad).mkdir()
    _surec(kok, 1111, UVICORN_ARGV, yas_sn=86_400)
    monkeypatch.setattr(watchdog, "PROC_KOK", str(kok))
    monkeypatch.setattr(watchdog, "_clk_tck", lambda: TCK)
    return kok


def _kullanim(kullanilan_g: float, toplam_g: float = 157.0) -> types.SimpleNamespace:
    toplam = int(toplam_g * G)
    bos = int((toplam_g - kullanilan_g) * G)
    return types.SimpleNamespace(total=toplam, used=toplam - bos, free=bos)


@pytest.fixture
def diskli(sandbox_state, monkeypatch, tmp_path):
    yol = tmp_path / "opt_veri"
    yol.mkdir()
    monkeypatch.setattr(watchdog, "VERI_DISK_YOLU", str(yol))
    monkeypatch.setattr(watchdog, "_now", lambda: 1_800_000_000.0)  # sabit gün (UTC)
    return yol


def _kullanimi_ayarla(monkeypatch, kullanilan_g: float) -> None:
    monkeypatch.setattr(watchdog.shutil, "disk_usage", lambda _yol: _kullanim(kullanilan_g))


def _satir() -> dict:
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    return (doc.get("mekanizmalar") or {}).get(watchdog._VERI_DISK_MEK_ADI) or {}


ASIM = watchdog.VERI_DISK_ESIK_G + 3       # sahneler eşiğe GÖRELİ (v414 dersi: literal sessizce kayar)


# =============================================================================================
# TESPİT BİRİMİ — `geridolum_is_durumu()` sahte /proc üstünde
# =============================================================================================

def test_tespit_surucu_kosuyor_sure_olculur(proc):
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=30 * 60)
    d = watchdog.geridolum_is_durumu()
    assert d["kosuyor"] is True
    assert d["pid"] == 4242
    assert d["sure_sn"] == pytest.approx(1800.0, abs=0.1)
    assert d["olculemedi_neden"] is None


def test_tespit_tuzak_surecler_is_sayilmaz(proc):
    """Adında geridolum.py geçen ama SÜRÜCÜ OLMAYAN süreçler: editör, py_compile, işçinin pilot
    çocuğu. Sürücü imzası = argv[0] python + argv[1] betik (birim ExecStart'ının biçimi)."""
    _surec(proc, 5001, ["vim", "/opt/veri/geridolum.py"], yas_sn=60)
    _surec(proc, 5002, ["/usr/bin/python3", "-m", "py_compile", "/opt/veri/geridolum.py"], yas_sn=60)
    _surec(proc, 5003, ["/opt/veri/pilot-venv/bin/python", "/opt/veri/pilot.py", "--gun",
                        "2026-09-29", "--kapsam", "/opt/veri/kapsam.txt"], yas_sn=60)
    _surec(proc, 5004, ["less", "geridolum.py"], yas_sn=60)
    d = watchdog.geridolum_is_durumu()
    assert d == {"kosuyor": False, "pid": None, "sure_sn": None, "olculemedi_neden": None}


def test_tespit_comm_parantez_ve_bosluk_tasisa_da_ayristirilir(proc):
    """`comm` alanı boşluk ve `)` taşıyabilir — ayrıştırma SON `)`ten sonra yapılır."""
    _surec(proc, 4243, SURUCU_ARGV, yas_sn=600, comm="py (x) thon")
    d = watchdog.geridolum_is_durumu()
    assert d["kosuyor"] is True and d["sure_sn"] == pytest.approx(600.0, abs=0.1)


def test_tespit_birden_fazla_surucu_en_eskisi_secilir(proc):
    """flock ikinciyi saniyeler içinde çıkarır ama o anda iki süreç görünebilir — TAŞMA için
    temkinli taraf EN ESKİsidir."""
    _surec(proc, 6001, SURUCU_ARGV, yas_sn=5)
    _surec(proc, 6002, SURUCU_ARGV, yas_sn=3 * 3600)
    d = watchdog.geridolum_is_durumu()
    assert d["pid"] == 6002 and d["sure_sn"] == pytest.approx(3 * 3600.0, abs=0.1)


def test_tespit_proc_yok_olculemedi(monkeypatch, tmp_path):
    monkeypatch.setattr(watchdog, "PROC_KOK", str(tmp_path / "yok"))
    d = watchdog.geridolum_is_durumu()
    assert d["kosuyor"] is False
    assert d["olculemedi_neden"] and "listelenemedi" in d["olculemedi_neden"]


def test_tespit_hic_surec_gorunmuyor_olculemedi(monkeypatch, tmp_path):
    """Gerçek bir /proc EN AZ bekçinin kendi sürecini gösterir; boş liste 'iş yok' değil
    'süreç tablosu görünmüyor'dur (örn. yanlış kök ya da ad alanı yalıtımı)."""
    kok = tmp_path / "proc_bos"
    kok.mkdir()
    monkeypatch.setattr(watchdog, "PROC_KOK", str(kok))
    d = watchdog.geridolum_is_durumu()
    assert d["kosuyor"] is False and d["olculemedi_neden"]


def test_tespit_stat_bozuk_olculemedi_pid_kayitli(proc):
    _surec(proc, 4244, SURUCU_ARGV, stat="bozuk satir parantezsiz\n")
    d = watchdog.geridolum_is_durumu()
    assert d["kosuyor"] is False, "süresi ölçülemeyen iş 'koşuyor' SAYILAMAZ — taşma denetlenemez"
    assert d["pid"] == 4244
    assert d["olculemedi_neden"] and "ölçülemedi" in d["olculemedi_neden"]


def test_tespit_negatif_sure_olculemedi(proc):
    """Başlangıç tiki açılış süresinden BÜYÜK (tutarsız saat tabanı): negatif süre 'taşmadı'
    diye okunursa hüküm SONSUZA dek atlanırdı — ölçülemedi sayılır."""
    _surec(proc, 4246, SURUCU_ARGV, yas_sn=-600)
    d = watchdog.geridolum_is_durumu()
    assert d["kosuyor"] is False and d["pid"] == 4246
    assert d["olculemedi_neden"] and "negatif" in d["olculemedi_neden"]


def test_tespit_uptime_yok_olculemedi(proc):
    _surec(proc, 4245, SURUCU_ARGV, yas_sn=60)
    (proc / "uptime").unlink()
    d = watchdog.geridolum_is_durumu()
    assert d["kosuyor"] is False and d["olculemedi_neden"]


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root izin bitlerini yok sayar — izin hatası sahnelenemez")
def test_tespit_izin_yok_eslesme_yoksa_neden_yazilir(proc):
    _surec(proc, 7001, ["/usr/sbin/sshd"], yas_sn=60)
    (proc / "7001" / "cmdline").chmod(0)
    try:
        d = watchdog.geridolum_is_durumu()
    finally:
        (proc / "7001" / "cmdline").chmod(0o644)
    assert d["kosuyor"] is False
    assert d["olculemedi_neden"] and "okunamadı" in d["olculemedi_neden"]


def test_tespit_yorumlayici_bayragi_eslesmez_alarm_calar(diskli, proc, alarmlar, monkeypatch):
    """KARAR (düzeltme turu 1, M5b): `python -u …/geridolum.py` (argv[1] = "-u") sürücü SAYILMAZ →
    koşmuyor → alarm ÇALAR (güvenli yön). Canlı ExecStart bayraksızdır (Rol-1 A1 ölçümü 2026-09-30:
    `/opt/veri/pilot-venv/bin/python /opt/veri/geridolum.py`); birim bir gün bayrak alırsa ayrışma
    çivisi (`test_ayrisma_betik_adi_birim_execstart_ile_ayni`) öter ve imza birlikte güncellenir."""
    _surec(proc, 4250, ["/opt/veri/pilot-venv/bin/python", "-u", "/opt/veri/geridolum.py"],
           yas_sn=10 * 60)
    d = watchdog.geridolum_is_durumu()
    assert d == {"kosuyor": False, "pid": None, "sure_sn": None, "olculemedi_neden": None}
    _kullanimi_ayarla(monkeypatch, ASIM)
    watchdog.check_veri_disk_and_alarm()
    assert len(alarmlar) == 1 and alarmlar[0]["is_kosuyor"] is False


def test_tespit_surec_yarisi_bitmis_surec_yok_sayilir(proc):
    """Listeleme ile okuma arasında biten süreç (cmdline YOK) normal yarıştır — ölçüm eksilmez."""
    (proc / "8001").mkdir()
    d = watchdog.geridolum_is_durumu()
    assert d == {"kosuyor": False, "pid": None, "sure_sn": None, "olculemedi_neden": None}


# =============================================================================================
# DAVRANIŞ — `check_veri_disk_and_alarm()`
# =============================================================================================

def test_1_is_kosuyor_esik_asildi_alarm_yok_atlama_sayilir(diskli, proc, alarmlar, monkeypatch):
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=20 * 60)
    _kullanimi_ayarla(monkeypatch, ASIM)
    rep = watchdog.check_veri_disk_and_alarm()
    assert alarmlar == [], "iş koşarken eşik HÜKMÜ verilmez (operatör 2026-09-30)"
    assert rep["atlandi"] is True and rep["is_durumu"]["kosuyor"] is True
    satir = _satir()
    assert satir.get("atlandi_is_kosuyor") == 1, "atlama SESSİZ olamaz (Bedel yasası)"
    assert satir.get("atlanan_tepe_g") == float(ASIM)
    assert int(satir.get("alarm") or 0) == 0
    watchdog.check_veri_disk_and_alarm()                 # bir sonraki poll — sayaç birikir
    assert _satir()["atlandi_is_kosuyor"] == 2
    assert alarmlar == []


def test_1b_atlanan_tepe_gunun_en_buyugunu_tutar(diskli, proc, alarmlar, monkeypatch):
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=20 * 60)
    for g in (ASIM, ASIM + 2, ASIM - 1):
        _kullanimi_ayarla(monkeypatch, g)
        watchdog.check_veri_disk_and_alarm()
    assert _satir()["atlanan_tepe_g"] == float(ASIM + 2)
    assert _satir()["atlandi_is_kosuyor"] == 3


def test_1c_api_alarm_gunlugu_atlama_sayacini_okur(diskli, proc, alarmlar, monkeypatch):
    """YASA 6: sayacın DIŞ okuyucusu `api._alarm_gunluk()` — satır projeksiyonu alanları AD AD
    seçer (genel değil), bu yüzden yeni alanlar oraya AÇIKÇA eklendi."""
    from meridian import api
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=20 * 60)
    _kullanimi_ayarla(monkeypatch, ASIM)
    watchdog.check_veri_disk_and_alarm()
    ag = api._alarm_gunluk()
    satir = ag["mekanizmalar"][watchdog._VERI_DISK_MEK_ADI]
    assert satir["atlandi_is_kosuyor"] == 1
    assert satir["atlanan_tepe_g"] == float(ASIM)
    assert ag["mekanizmalar"][watchdog._VERI_DISK_MEK_ADI]["alarm"] == 0


def test_2_is_kosmuyor_esik_asildi_alarm_ve_gunluk_tavan(diskli, proc, alarmlar, monkeypatch):
    _kullanimi_ayarla(monkeypatch, ASIM)
    rep = watchdog.check_veri_disk_and_alarm()
    watchdog.check_veri_disk_and_alarm()                 # aynı gün — mandal
    assert len(alarmlar) == 1
    a = alarmlar[0]
    assert a["token"] == "DISK_ESIK"
    assert a["kullanilan_g"] == float(ASIM) and a["esik_g"] == watchdog.VERI_DISK_ESIK_G
    assert "koşmuyor" in a["message"] and "KALICI" in a["message"]
    assert a["is_kosuyor"] is False and a["is_olculemedi_neden"] is None
    assert rep["atlandi"] is False
    satir = _satir()
    assert satir["alarm"] == 1 and satir["bastirilan"] == 1
    assert "atlandi_is_kosuyor" not in satir


def test_3_tasma_takili_is_alarm_calar_sure_metni(diskli, proc, alarmlar, monkeypatch):
    yas = watchdog.TASMA_SN + 17 * 60
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=yas)
    _kullanimi_ayarla(monkeypatch, ASIM)
    rep = watchdog.check_veri_disk_and_alarm()
    assert len(alarmlar) == 1, "TAŞMA: takılı iş körlük YARATMAZ — alarm normal kurallarla çalar"
    msg = alarmlar[0]["message"]
    assert f"{int(yas // 60)} dk'dır koşuyor" in msg
    assert alarmlar[0]["is_kosuyor"] is True and alarmlar[0]["is_pid"] == 4242
    assert alarmlar[0]["is_sure_sn"] == pytest.approx(yas, abs=0.1)
    assert rep["atlandi"] is False
    assert "atlandi_is_kosuyor" not in _satir()


def test_3b_tasma_siniri_kapsayici(diskli, proc, alarmlar, monkeypatch):
    """Sınır: `sure_sn >= TASMA_SN` taşmadır; bir saniye önce atlamadır."""
    _kullanimi_ayarla(monkeypatch, ASIM)
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=watchdog.TASMA_SN - 1)
    watchdog.check_veri_disk_and_alarm()
    assert alarmlar == [] and _satir()["atlandi_is_kosuyor"] == 1
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=watchdog.TASMA_SN)
    watchdog.check_veri_disk_and_alarm()
    assert len(alarmlar) == 1


def test_3c_tasma_alarmi_da_gunluk_tavana_tabi(diskli, proc, alarmlar, monkeypatch):
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=watchdog.TASMA_SN + 60)
    _kullanimi_ayarla(monkeypatch, ASIM)
    watchdog.check_veri_disk_and_alarm()
    watchdog.check_veri_disk_and_alarm()
    assert len(alarmlar) == 1 and _satir()["bastirilan"] == 1


def test_4_is_durumu_olculemedi_alarm_calar_neden_govdede(diskli, alarmlar, monkeypatch, tmp_path):
    monkeypatch.setattr(watchdog, "PROC_KOK", str(tmp_path / "proc_yok"))
    _kullanimi_ayarla(monkeypatch, ASIM)
    rep = watchdog.check_veri_disk_and_alarm()
    assert len(alarmlar) == 1, "ölçülemeyen iş durumu 'koşmuyor' SAYILIR — güvenli yön alarmdır"
    assert alarmlar[0]["is_olculemedi_neden"]
    assert "ÖLÇÜLEMEDİ" in alarmlar[0]["message"]
    assert rep["is_durumu"]["olculemedi_neden"]


def test_4b_surucu_gorundu_ama_suresi_olculemedi_alarm_calar(diskli, proc, alarmlar, monkeypatch):
    """Süreç VAR ama yaşı ölçülemiyor → taşma denetlenemez → koşmuyor sayılır, alarm çalar."""
    _surec(proc, 4242, SURUCU_ARGV, stat="bozuk\n")
    _kullanimi_ayarla(monkeypatch, ASIM)
    watchdog.check_veri_disk_and_alarm()
    assert len(alarmlar) == 1
    assert "atlandi_is_kosuyor" not in _satir()


def test_5_yol_yok_davranis_ayni_surec_tablosu_okunmaz(sandbox_state, alarmlar, monkeypatch,
                                                         tmp_path):
    monkeypatch.setattr(watchdog, "VERI_DISK_YOLU", str(tmp_path / "yok_boyle_bir_yer"))

    def _okunmamali():
        raise AssertionError("yol yokken süreç tablosu OKUNMAMALI")
    monkeypatch.setattr(watchdog, "geridolum_is_durumu", _okunmamali)
    rep = watchdog.check_veri_disk_and_alarm()
    assert rep == watchdog.veri_disk_report()
    assert rep["var"] is False and rep["olculemedi_neden"]
    assert alarmlar == []


def test_4c_tespit_beklenmedik_istisna_alarm_calar_tur_govdede(diskli, alarmlar, monkeypatch):
    """Düzeltme turu 1 (M4): tespitin BEKLENMEDİK istisnası hükmü durdurmaz. Sarılmasaydı istisna
    `check_and_alarm`ın genel yakalayıcısına düşer, yalnız `warn` basılır (bildirim zinciri YOK) ve
    alarm her poll'da yutulurdu. Gövdeye istisnanın TÜRÜ gider, DEĞERİ gitmez."""
    def _patlayan():
        raise RuntimeError("gizli-deger-xyz")
    monkeypatch.setattr(watchdog, "geridolum_is_durumu", _patlayan)
    _kullanimi_ayarla(monkeypatch, ASIM)
    rep = watchdog.check_veri_disk_and_alarm()
    assert len(alarmlar) == 1, "tespit düştü diye alarm YUTULAMAZ — koşmuyor sayılır"
    neden = alarmlar[0]["is_olculemedi_neden"]
    assert neden and "RuntimeError" in neden
    assert "gizli-deger-xyz" not in neden and "gizli-deger-xyz" not in alarmlar[0]["message"]
    assert "ÖLÇÜLEMEDİ" in alarmlar[0]["message"]
    assert alarmlar[0]["is_kosuyor"] is False and rep["atlandi"] is False


def test_1d_gun_donumunde_atlama_sayaclari_sifirlanir(diskli, proc, alarmlar, monkeypatch):
    """Düzeltme turu 1 (M5a): iki sayaç günlük defterin İÇİNDEdir — gün dönünce SIFIRDAN başlar
    (`_gunluk_oku` davranışı); dünün tepesi bugünün tepesi diye okunmaz."""
    gun = {"v": "2026-09-30"}
    monkeypatch.setattr(watchdog, "_bugun", lambda now=None: gun["v"])
    _surec(proc, 4242, SURUCU_ARGV, yas_sn=20 * 60)
    _kullanimi_ayarla(monkeypatch, ASIM + 2)
    watchdog.check_veri_disk_and_alarm()
    watchdog.check_veri_disk_and_alarm()
    assert _satir()["atlandi_is_kosuyor"] == 2 and _satir()["atlanan_tepe_g"] == float(ASIM + 2)
    gun["v"] = "2026-10-01"
    _kullanimi_ayarla(monkeypatch, ASIM)
    watchdog.check_veri_disk_and_alarm()
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    assert doc["gun"] == "2026-10-01"
    assert _satir()["atlandi_is_kosuyor"] == 1, "dünün sayacı bugüne taşındı"
    assert _satir()["atlanan_tepe_g"] == float(ASIM), "dünün tepesi bugüne taşındı"
    assert alarmlar == []


def test_esik_altinda_surec_tablosu_okunmaz_defter_yazilmaz(diskli, alarmlar, monkeypatch):
    """Ucuz yol: tespit YALNIZ eşik aşıldığında koşar (300 sn poll'unda boşuna /proc taranmaz)."""
    def _okunmamali():
        raise AssertionError("eşik altında süreç tablosu OKUNMAMALI")
    monkeypatch.setattr(watchdog, "geridolum_is_durumu", _okunmamali)
    _kullanimi_ayarla(monkeypatch, watchdog.VERI_DISK_ESIK_G - 5)
    rep = watchdog.check_veri_disk_and_alarm()
    assert rep["esik_asildi"] is False and alarmlar == []
    assert _satir() == {}


# =============================================================================================
# SABİTLER + KAYNAK SÖZLEŞMELERİ
# =============================================================================================

def test_sabitler_olculen_karar():
    assert watchdog.VERI_DISK_ESIK_G == 140, "eşik operatörün 2026-09-12 kararıdır — DOKUNULMAZ"
    assert watchdog.TASMA_SN == 2 * 3600, "taşma tavanı ölçülen normal koşumun (25–32 dk) ~4 katı"


def _execstart_argv(birim: pathlib.Path) -> list[str]:
    satirlar = [s.split("=", 1)[1].strip() for s in birim.read_text(encoding="utf-8").splitlines()
                if s.startswith("ExecStart=")]
    assert len(satirlar) == 1, f"{birim.name}: tek ExecStart bekleniyordu"
    return satirlar[0].split()


def test_ayrisma_betik_adi_birim_execstart_ile_ayni():
    """TEK KAYNAK: sürücünün kimliği birim dosyasının ExecStart'ıdır. `watchdog.GERIDOLUM_BETIK`
    bir KOPYADIR (canlıda deploy/ ağacı okunamaz); ayrışırsa tespit sessizce 'koşmuyor' der."""
    argv = _execstart_argv(BIRIM_KOK / "meridian-geridolum.service")
    assert pathlib.PurePath(argv[0]).name.startswith("python"), argv
    assert pathlib.PurePath(argv[1]).name == watchdog.GERIDOLUM_BETIK, argv
    assert (BIRIM_KOK / watchdog.GERIDOLUM_BETIK).is_file()


def _yonergeler(metin: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in metin.splitlines():
        s = s.strip()
        if not s or s.startswith(("#", ";", "[")) or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out.setdefault(k.strip(), []).append(v.strip())
    return out


def test_yontem_onculu_birim_sertlestirmesi():
    """(a) /proc taramasının ÖNCÜLÜ: bekçinin koştuğu meridian.service (+drop-in'ler) süreç
    tablosunu gizlemez ve iki birim AYNI kullanıcıdadır. Sertleştirme turu (meridian.service
    başlığı 'Tur-3 kalemi') bunlardan birini eklerse tespit KÖR kalır — bu çivi öter ve yöntem
    yeniden seçilir."""
    ana = _yonergeler((BIRIM_KOK / "meridian.service").read_text(encoding="utf-8"))
    for dropin in sorted((BIRIM_KOK / "meridian.service.d").glob("*.conf")):
        for k, v in _yonergeler(dropin.read_text(encoding="utf-8")).items():
            ana.setdefault(k, []).extend(v)
    for yasak in ("PrivatePIDs", "ProcSubset", "ProtectProc", "PrivateUsers"):
        assert yasak not in ana, f"meridian.service {yasak} taşıyor — /proc tespiti kör kalır"
    isb = _yonergeler((BIRIM_KOK / "meridian-geridolum.service").read_text(encoding="utf-8"))
    assert ana.get("User") == isb.get("User") == ["ubuntu"]


def test_tespit_alt_surec_acmaz_isin_kilidine_dokunmaz():
    """(b) systemctl alt süreci ve (c) flock yoklaması SEÇİLMEDİ: tespit fonksiyonu subprocess/os
    çağrısı yapmaz; watchdog işin kilit dosyasını ANMAZ ve fcntl ithal etmez."""
    kaynak = (SRC / "meridian" / "watchdog.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    fn = next(n for n in agac.body
              if isinstance(n, ast.FunctionDef) and n.name == "geridolum_is_durumu")
    adlar = {getattr(c.func, "attr", getattr(c.func, "id", None))
             for c in ast.walk(fn) if isinstance(c, ast.Call)}
    assert not adlar & {"run", "Popen", "check_output", "system", "popen", "flock", "lockf"}
    assert "geridolum.kilit" not in kaynak
    assert not re.search(r"^\s*import fcntl|^\s*from fcntl", kaynak, re.M)


def test_bayat_mesaj_metni_gitti():
    """09-12'den beri eşik geri dolumun 120 G tavanının erken uyarısı DEĞİL — mesaj gerçeğe çekildi."""
    agac = ast.parse((SRC / "meridian" / "watchdog.py").read_text(encoding="utf-8"))
    fn = next(n for n in agac.body
              if isinstance(n, ast.FunctionDef) and n.name == "check_veri_disk_and_alarm")
    metin = ast.get_source_segment((SRC / "meridian" / "watchdog.py").read_text(encoding="utf-8"),
                                   fn) or ""
    assert "tavanına yaklaşıyor" not in metin


# ---- düzeltme turu 1 (I1): OPERATÖRÜN GÖRDÜĞÜ metinler 09-12 + TSK-259 gerçeğini anlatır --------

def test_obs_disk_esik_serhi_bayat_degil():
    """`meridian/obs.py` ALARM_DISK_ESIK şerhi RUNBOOK'un "Belirti" (satır sonu) ve "Neden ayrı bir
    sınıf" (üstteki blok) satırlarına ÜRETİLİR (`ops/runbook_uret.py::alarm_envanteri`) — bayat
    kalırsa RUNBOOK aynı bölümde mesaj şablonuyla ÇELİŞİR."""
    satirlar = (SRC / "meridian" / "obs.py").read_text(encoding="utf-8").splitlines()
    i = next(n for n, s in enumerate(satirlar) if s.startswith("ALARM_DISK_ESIK ="))
    blok = []
    j = i - 1
    while j >= 0 and satirlar[j].strip().startswith("#"):
        blok.append(satirlar[j])
        j -= 1
    metin = " ".join(reversed(blok)) + " " + satirlar[i]
    for bayat in ("tavanına yaklaşıyor", "10 G ÖNCESİNDE", "erken uyarı"):
        assert bayat not in metin, f"obs.py ALARM_DISK_ESIK şerhi bayat: {bayat!r}"
    for gercek in ("140 G", "KALICI", "TSK-259"):
        assert gercek in metin, f"obs.py ALARM_DISK_ESIK şerhinde {gercek!r} yok"


def test_pano_kapasite_karti_bayat_degil():
    """`meridian/web/app.js` `kapasite` sınıfı (DISK_ESIK'in pano kartı) operatörün alarmı okuduğu
    yerdir: 09-12'den beri eşik 140 G, alarm yalnız KALICI doluluğu hükme bağlar."""
    js = (SRC / "meridian" / "web" / "app.js").read_text(encoding="utf-8")
    bas = js.index("\n  kapasite: {")
    son = js.index("\n  sir_kasasi: {", bas)
    kart = js[bas:son]
    for bayat in ("110 G", "tavanına yaklaşıyor", "kalıcı+geçici", "10 G ÖNCE"):
        assert bayat not in kart, f"app.js kapasite kartı bayat: {bayat!r}"
    for gercek in ("140 G", "KALICI", "atlandi_is_kosuyor", "/api/diagnostics"):
        assert gercek in kart, f"app.js kapasite kartında {gercek!r} yok"

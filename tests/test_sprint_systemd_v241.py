"""v241 — SPRINT ARTIK KENDİ SYSTEMD BİRİMİNDE DOĞAR (worker restart'ı onu öldüremez).

ÖLÇÜLEN KÖK NEDEN (ölüm-anı yakalayıcısı, üç ölümde aynı desen): `sprint.start()` çocuğu
`subprocess.Popen(..., start_new_session=True)` ile doğuruyordu. `start_new_session` yeni bir OTURUM
açar ama systemd'nin CGROUP'undan ÇIKARMAZ; `KillMode=control-group` varsayılanı yüzünden
`systemctl restart meridian` cgroup'taki HER süreci — sprint çocuğu dahil — öldürüyordu.
    14:50:02 sprint 113/531 → 14:54:14 worker yeni pid → 14:54:16 ORPHAN → 14:54:22 pid yok
    (dmesg'de OOM YOK, traceback YOK: çökmedi, ÖLDÜRÜLDÜ)

BU DOSYA NE ÇİVİLER — düzeltmenin SÖZLEŞMESİ, systemd'siz bir makinede (yerel macOS) ölçülebilir hâlde:
  (1) systemd yolu VARSA seçilir; `Popen` ÇAĞRILMAZ (çift sprint = aynı kum havuzuna iki yazar).
  (2) Yol YOKSA `Popen`a düşülür ama SESSİZCE DEĞİL: `sprint_systemd_yok` olayı + ADLI sebep.
  (3) `kosum_yolu` damgası her iki yolda da doğrudur VE çocuğun yazımında hayatta kalır (C15 sınıfı).
  (4) `status()` alan sözleşmesi DEĞİŞMEDİ — pano/kadans/yetim mekanizması aynı alanları okur.
  (5) `stop()` her iki yolda da çalışır: systemd yolunda BİRİMİ durdurur (cgroup'un tamamı), popen
      yolunda pid'e SIGTERM; birim durdurulamazsa pid'e DÜŞER ve bunu KAYDA GEÇİRİR.

SAHTE `systemctl` GERÇEK BİR ÇALIŞTIRILABİLİRDİR (PATH'e konur), monkeypatch'lenmiş bir fonksiyon
değil: ölçülmek istenen şeyin yarısı KOMUT KURULUMUDUR (`sudo -n systemctl start <birim>`) ve onu
saplamak, ölçüyü kendi iddiasından mahrum bırakırdı. Gerçek `subprocess` çağrılır, gerçek argümanlar
diske yazılır ve test onları okur.

CANLIYA HİÇBİR ŞEY YAZILMAZ: her test `sandbox_state` içinde koşar, gerçek `systemctl`/`sudo`
PATH'ten DÜŞÜRÜLÜR (sahteleri öne alınır) ve `meridian.sprint_run` alt süreci hiç doğmaz.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from meridian import sprint, sprint_run, store

# Gerçek Popen, sahte katman devreye girmeden önce yakalanır: sahtemiz SPRINT ÇOCUĞUNU keser,
# diğer her çağrıyı (subprocess.run → systemctl) gerçeğine devreder. Yoksa `subprocess.run`
# sahtemizin içine düşer ve sahte `systemctl` hiç koşamazdı.
GERCEK_POPEN = subprocess.Popen

SAHTE_SYSTEMCTL = """#!/bin/sh
printf '%s\\n' "$*" >> "$SAHTE_KAYIT"
case "$1" in
  show)  printf '%s\\n' "${SAHTE_MAINPID:-0}"; exit 0 ;;
  start) exit "${SAHTE_START_RC:-0}" ;;
  stop)  exit "${SAHTE_STOP_RC:-0}" ;;
esac
exit 0
"""
# `sudo -n <komut>` → doğrudan komutu koştur. Üretim komut kurulumunun (`sudo -n systemctl …`)
# aynen sınanabilmesi için var: `MERIDIAN_SPRINT_SYSTEMCTL` seam'iyle sudo'yu atlasaydık, canlıda
# gerçekten koşacak komutu HİÇ ölçmemiş olurduk.
SAHTE_SUDO = """#!/bin/sh
[ "$1" = "-n" ] && shift
exec "$@"
"""


class _CocukTaklidi:
    """`Popen` dönüşünün sprint'in kullandığı TEK yüzeyi: `.pid`."""
    def __init__(self, pid: int = 424242):
        self.pid = pid


@pytest.fixture
def ortam(sandbox_state, tmp_path, monkeypatch):
    """Sahte systemctl/sudo + birim dizini + kum havuzu köküne hizalanmış yol kapısı."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for ad, govde in (("systemctl", SAHTE_SYSTEMCTL), ("sudo", SAHTE_SUDO)):
        p = bin_dir / ad
        p.write_text(govde)
        p.chmod(0o755)
    kayit = tmp_path / "systemctl.log"
    kayit.write_text("")
    monkeypatch.setenv("PATH", str(bin_dir))          # gerçek systemctl/sudo ERİŞİLEMEZ
    monkeypatch.setenv("SAHTE_KAYIT", str(kayit))
    monkeypatch.delenv("MERIDIAN_SPRINT_SYSTEMCTL", raising=False)
    # Birim ARANAN dizini + kurulu şablon (testler `birim_kaldir()` ile yokluğu kurar).
    birim_dizin = tmp_path / "systemd"
    birim_dizin.mkdir()
    (birim_dizin / sprint.BIRIM_DOSYA_ADI).write_text("# sahte şablon birim\n")
    monkeypatch.setattr(sprint, "BIRIM_ARANAN_DIZINLER", (str(birim_dizin),))
    # YOL KAPISI: birim `<BIRIM_KOK>/state/sprint/<sid>/sprint.env` okur. Kum havuzu tmp'de olduğu
    # için kök de oraya hizalanır — kapının KENDİSİ ayrı bir testte (yol_uyusmazligi) ölçülür.
    monkeypatch.setattr(sprint, "BIRIM_KOK", str(Path(sandbox_state).resolve().parent))
    monkeypatch.setattr(sprint, "MAINPID_BEKLE_SN", 0.0)     # geri çekilme uykusu ölçüye girmiyor

    cocuklar: list[list[str]] = []

    def sahte_popen(args, *a, **kw):
        if any("meridian.sprint_run" in str(x) for x in args):
            cocuklar.append([str(x) for x in args])
            return _CocukTaklidi()
        return GERCEK_POPEN(args, *a, **kw)          # systemctl/sudo GERÇEKTEN koşar
    monkeypatch.setattr(sprint.subprocess, "Popen", sahte_popen)

    class Ortam:
        state = sandbox_state
        popen_cagrilari = cocuklar

        @staticmethod
        def systemctl_satirlari() -> list[str]:
            return [s for s in kayit.read_text().splitlines() if s.strip()]

        @staticmethod
        def birim_kaldir() -> None:
            (birim_dizin / sprint.BIRIM_DOSYA_ADI).unlink()

        @staticmethod
        def olaylar(ad: str) -> list[dict]:
            f = sandbox_state / "events.jsonl"
            if not f.exists():
                return []
            return [e for e in (json.loads(x) for x in f.read_text().splitlines() if x.strip())
                    if e.get("event") == ad]

    monkeypatch.setenv("SAHTE_MAINPID", str(os.getpid()))    # canlı pid → status().active True
    return Ortam


def _ortam_dosyasi_coz(metin: str) -> dict:
    """systemd'nin TEK TIRNAK semantiğini taklit eden ayrıştırıcı: `KEY='deger'` → {KEY: deger}.
    Tek tırnak içinde systemd hiçbir şeyi yorumlamaz — testin ayrıştırıcısı da yorumlamamalı."""
    out = {}
    for satir in metin.splitlines():
        if not satir.strip():
            continue
        k, _, v = satir.partition("=")
        assert v.startswith("'") and v.endswith("'"), f"değer tek tırnaklı değil: {satir}"
        out[k] = v[1:-1]
    return out


# ============================ (1) SYSTEMD YOLU SEÇİLİR ============================

def test_systemd_yolu_secilir_ve_popen_CAGRILMAZ(ortam):
    """ASIL İDDİA: birim kuruluysa sprint `sudo -n systemctl start meridian-sprint@<sid>.service`
    ile doğar ve ESKİ `Popen` yolu HİÇ çalışmaz."""
    res = sprint.start({"k_max": 3, "budget": 12})
    assert res["started"] and res["kosum_yolu"] == "systemd", res
    assert res["birim"] == f"meridian-sprint@{res['sid']}.service"
    assert res["pid"] == os.getpid(), "pid systemd'nin MainPID'inden alınmalı"
    assert ortam.popen_cagrilari == [], "systemd yolu seçilmişken çocuk süreç doğdu (ÇİFT SPRINT)"
    baslat = [s for s in ortam.systemctl_satirlari() if s.startswith("start ")]
    assert baslat == [f"start meridian-sprint@{res['sid']}.service"], ortam.systemctl_satirlari()


def test_ortam_dosyasi_conf_ve_uc_degiskeni_TASIR(ortam):
    """Çocuğun iki argümanı ve üç ortam değişkeni birim dosyasına ORTAM DOSYASIYLA geçer.
    QUOTING SÖZLEŞMESİ: JSON tek tırnak içinde taşınır — çift tırnakla yazılsaydı systemd içteki
    `"`leri söker ve çocuk `json.loads`ta patlardı (sessiz bozulma sınıfı)."""
    res = sprint.start({"k_max": 2, "budget": 6})
    env_dosyasi = Path(res["sbroot"]) / sprint.ORTAM_DOSYASI
    assert env_dosyasi.exists(), "birim `EnvironmentFile=` ile bu dosyayı okuyacak"
    e = _ortam_dosyasi_coz(env_dosyasi.read_text())
    assert json.loads(e["MERIDIAN_SPRINT_CONF"]) == {"k_max": 2, "budget": 6}
    assert " " not in e["MERIDIAN_SPRINT_CONF"], "conf BOŞLUKSUZ olmalı (`$VAR` bölünmesine karşı)"
    assert e["MERIDIAN_SPRINT_SBROOT"] == res["sbroot"]
    # sprint.py:297-298 ile BİREBİR üçlü
    assert e["MERIDIAN_ROOT"] == res["sbroot"] and e["MERIDIAN_BROKER"] == "internal"
    assert e["MERIDIAN_SPRINT_STATUS"].endswith(sprint.STATUS_FILE)


def test_ortam_dosyasi_SIRRI_TASIMAZ_ama_arama_ayarlarini_TASIR(ortam, monkeypatch):
    """DARALTMA BİLİNÇLİ VE İKİ YÖNLÜ. Bugünkü `Popen` yolu worker'ın TÜM ortamını (sırlar dahil)
    çocuğa akıtıyor. Birim yolu allowlist kullanır: davranışı ÖLÇÜLEN iki arama değişkeni taşınır,
    pano token'ı taşınmaz."""
    monkeypatch.setenv("MERIDIAN_DASH_TOKEN", "cok-gizli-jeton")
    monkeypatch.setenv("MERIDIAN_PARALLEL_PROBES", "1")
    monkeypatch.setenv("MERIDIAN_SEARCH_MAX_MIN", "60")
    res = sprint.start()
    metin = (Path(res["sbroot"]) / sprint.ORTAM_DOSYASI).read_text()
    assert "cok-gizli-jeton" not in metin and "MERIDIAN_DASH_TOKEN" not in metin
    e = _ortam_dosyasi_coz(metin)
    assert e["MERIDIAN_PARALLEL_PROBES"] == "1" and e["MERIDIAN_SEARCH_MAX_MIN"] == "60"


def test_ortam_metni_tasinamayan_degeri_REDDEDER():
    """Tek tırnaklı bir değer sessizce kırpılmaz/kaçırılmaz: taşınamıyorsa systemd yolu seçilmez
    (çağıran `Popen`a düşer ve sebebini yazar). Uydurma bir dönüşüm, sessiz bir arıza olurdu."""
    assert sprint._ortam_metni({"A": "duz"}) == "A='duz'\n"
    with pytest.raises(ValueError):
        sprint._ortam_metni({"A": "tek'tirnak"})
    with pytest.raises(ValueError):
        sprint._ortam_metni({"A": "satir\nsonu"})


def test_tetik_komutu_uretimde_sudo_n_systemctl(ortam):
    """Komut kurulumu ÇİVİLİ: `-n` (parola İSTEME, hızlı başarısız ol) pazarlığa açık değildir —
    bekleyen bir tetik zamanlayıcı thread'ini kilitlerdi."""
    komut, sebep = sprint._systemctl_komutu()
    assert sebep is None and komut is not None
    assert [Path(komut[0]).name, komut[1], Path(komut[2]).name] == ["sudo", "-n", "systemctl"]


def test_tetik_komutu_seam_ile_degistirilebilir(ortam, monkeypatch):
    """`MERIDIAN_SPRINT_SYSTEMCTL` seam'i: `NoNewPrivileges=true` sudo'yu bloklarsa operatörün
    ikinci yolu (polkit + busctl) KOD DEĞİŞİKLİĞİ İSTEMESİN diye var."""
    monkeypatch.setenv("MERIDIAN_SPRINT_SYSTEMCTL", "/usr/bin/busctl --sistem çağır")
    komut, sebep = sprint._systemctl_komutu()
    assert sebep is None and komut == ["/usr/bin/busctl", "--sistem", "çağır"]


# ============================ (2) DÜŞÜŞ GÖRÜNÜRDÜR ============================

def test_birim_yoksa_POPENA_DUSER_ve_OLAY_YAYINLAR(ortam):
    """FAIL-OPEN DEĞİL, FAIL-VISIBLE: eski yol çalışmaya devam eder ama sebebi ADIYLA kayda geçer —
    yoksa "sprint neden yine öldü?" sorusu bir sonraki turda yine tahminle cevaplanırdı."""
    ortam.birim_kaldir()
    res = sprint.start({"k_max": 3, "budget": 12})
    assert res["started"] and res["kosum_yolu"] == "popen" and res["birim"] is None
    assert res["pid"] == 424242, "düşüş yolunda pid `Popen`dan gelir"
    olay = ortam.olaylar("sprint_systemd_yok")
    assert olay and olay[-1]["sebep"] == "birim_kurulu_degil", olay
    assert olay[-1]["level"] == "warn" and "cgroup" in olay[-1]["detail"].lower()
    # KOMUT BİREBİR AYNI KALIR (birim dosyasındaki ExecStart'ın kaynağı da budur)
    argv = ortam.popen_cagrilari[-1]
    assert argv[1:3] == ["-m", "meridian.sprint_run"] and argv[3] == res["sbroot"]
    assert json.loads(argv[4]) == {"k_max": 3, "budget": 12}
    assert [s for s in ortam.systemctl_satirlari() if s.startswith("start ")] == []


def test_yol_uyusmazligi_systemd_yolunu_REDDEDER(ortam, monkeypatch):
    """KAPI: birim `<BIRIM_KOK>/state/sprint/<sid>/sprint.env` okur. Kum havuzu başka bir kökteyse
    birim BAŞKA (ya da olmayan) bir dosyadan ortam okurdu — sprint yanlış kökle koşardı."""
    monkeypatch.setattr(sprint, "BIRIM_KOK", "/baska/bir/kok")
    res = sprint.start()
    assert res["kosum_yolu"] == "popen"
    olay = ortam.olaylar("sprint_systemd_yok")[-1]
    assert olay["sebep"] == "yol_uyusmazligi" and "/baska/bir/kok" in olay["ayrinti"]
    assert not (Path(res["sbroot"]) / sprint.ORTAM_DOSYASI).exists(), "kapı YAZIMDAN ÖNCE gelmeli"


def test_tetik_hata_dondurse_de_birim_kosuyorsa_POPEN_YOK(ortam, monkeypatch):
    """ÇİFT-SPRINT KAPISI. Tetik komutu rc≠0 dönse bile birim ayakta olabilir; ikinci bir süreç
    doğurmak aynı kum havuzuna İKİ YAZAR demektir ve ölçümün kendisini çöpe atardı."""
    monkeypatch.setenv("SAHTE_START_RC", "1")
    res = sprint.start()
    assert res["kosum_yolu"] == "systemd" and res["pid"] == os.getpid()
    assert ortam.popen_cagrilari == [], "birim koşarken çocuk süreç doğdu (ÇİFT SPRINT)"


def test_tetik_hata_dondurur_ve_birim_de_kosmuyorsa_POPENA_DUSER(ortam, monkeypatch):
    """Karşı yön: rc≠0 VE MainPID=0 → koşan bir şey yok, düşüş güvenli ve sebebi adlı."""
    monkeypatch.setenv("SAHTE_START_RC", "1")
    monkeypatch.setenv("SAHTE_MAINPID", "0")
    res = sprint.start()
    assert res["kosum_yolu"] == "popen" and ortam.popen_cagrilari
    assert ortam.olaylar("sprint_systemd_yok")[-1]["sebep"] == "baslatma_hatasi"


def test_systemctl_hic_yoksa_sebep_ADIYLA_yazilir(ortam, monkeypatch, tmp_path):
    """Yerel geliştirme (macOS) yolu: systemd YOK → düşüş, ama "olmadı" değil "systemctl_yok"."""
    bos = tmp_path / "bos_bin"
    bos.mkdir()
    monkeypatch.setenv("PATH", str(bos))
    res = sprint.start()
    assert res["kosum_yolu"] == "popen"
    assert ortam.olaylar("sprint_systemd_yok")[-1]["sebep"] == "systemctl_yok"


# ============================ (3) DAMGA DOĞRU VE KALICI ============================

def test_kosum_yolu_damgasi_durum_dosyasina_yazilir(ortam):
    sprint.start()
    st = store.read_json(sprint.STATUS_FILE, {})
    assert st["kosum_yolu"] == "systemd" and st["birim"].startswith("meridian-sprint@")


def test_damga_COCUGUN_YAZIMINDA_hayatta_kalir(ortam):
    """C15 SINIFI. Çocuk (`sprint_run`) durum dosyasını KENDİ payload'ıyla yeniden yazar; damga
    `STAMP_KEYS`e eklenmeseydi ilk ilerleme yazımında (saniyeler içinde) yok olurdu ve operatörün
    doğrulama adımı ("kosum_yolu 'systemd' mi?") HİÇBİR ZAMAN yeşil okuyamazdı."""
    res = sprint.start()
    yol = str((ortam.state / sprint.STATUS_FILE).resolve())
    korunan = sprint_run._damgayi_koru(yol, {"sid": res["sid"], "phase": "baseline", "progress": 8})
    assert korunan["kosum_yolu"] == "systemd" and korunan["birim"] == res["birim"]
    assert korunan["n_hyp_at_start"] == res["n_hyp_at_start"]      # eski damga da yerinde
    assert {"kosum_yolu", "birim"} <= set(sprint_run.STAMP_KEYS)


# ============================ (4) status() SÖZLEŞMESİ DEĞİŞMEDİ ============================

def test_status_alan_sozlesmesi_DEGISMEDI(sandbox_state):
    """Pano, kadans (`should_run`), yetim göstergesi ve watchdog `_sprint_liveness` bu alanları
    okur. v241 pid'in KAYNAĞINI değiştirdi (systemd MainPID), ŞEMASINI değil: dosyadaki alanlar
    aynen geri döner ve status() TAM OLARAK yedi türetilmiş alan ekler."""
    dosya_alanlari = {"pid": 999999, "sid": "sid-x", "phase": "baseline", "started_at": "2026-08-13T00:00:00+00:00",
                      "cfg": {"k_max": 3, "budget": 12}, "sbroot": "/x/y", "eval_start": sprint.EVAL_START,
                      "cutoff": sprint.CUTOFF, "n_hyp_at_start": 7}
    store.write_json(sprint.STATUS_FILE, dosya_alanlari)
    st = sprint.status()
    for k, v in dosya_alanlari.items():
        assert st[k] == v, f"dosya alanı '{k}' status()'ta değişti"
    assert set(st) - set(dosya_alanlari) == {"active", "orphan", "orphan_note", "runs",
                                             "runs_ledger", "runs_kaynak", "runs_note"}
    assert st["active"] is False and st["orphan"] is True        # ölü pid + terminal olmayan faz


def test_status_systemd_pidini_aynen_okur(ortam):
    """systemd altında çocuk BİZİM çocuğumuz DEĞİLDİR (waitpid ChildProcessError verir) — canlılık
    yoklaması yine de `os.kill(pid, 0)` ile çalışır: ikisi de `ubuntu` kullanıcısındadır."""
    sprint.start()
    st = sprint.status()
    assert st["pid"] == os.getpid() and st["active"] is True and st["orphan"] is False


# ============================ (5) stop() HER İKİ YOLDA DA ÇALIŞIR ============================

@pytest.fixture
def kill_kaydi(monkeypatch):
    """`os.kill` KAYDEDİLİR ve HİÇBİR ZAMAN gerçek sinyal göndermez (test koşucusunu vurmasın)."""
    cagrilar: list[tuple] = []

    def sahte_kill(pid, sig):
        cagrilar.append((pid, sig))
        raise ProcessLookupError("sahte: süreç yok")
    monkeypatch.setattr(sprint.os, "kill", sahte_kill)
    return cagrilar


def _durum_yaz(state, *, yol, pid=999999, sid="20260813-151752"):
    sb = state / "sprint" / sid / "state"
    sb.mkdir(parents=True, exist_ok=True)
    store.write_json(sprint.STATUS_FILE,
                     {"pid": pid, "sid": sid, "phase": "baseline", "sbroot": str(sb.parent),
                      "kosum_yolu": yol, "birim": (sprint._birim_adi(sid) if yol == "systemd" else None)})
    return sb


def test_stop_systemd_yolunda_BIRIMI_durdurur(ortam, kill_kaydi):
    """`os.kill(pid, 15)` YETMEZ: havuz işçileri birimin cgroup'unda yaşamaya devam ederdi
    (Restart=no olduğu için systemd de toplamaz). `systemctl stop` cgroup'un TAMAMINI indirir."""
    sb = _durum_yaz(ortam.state, yol="systemd")
    res = sprint.stop()
    assert res["stopping"] and res["kosum_yolu"] == "systemd"
    assert [s for s in ortam.systemctl_satirlari() if s.startswith("stop ")] == \
        ["stop meridian-sprint@20260813-151752.service"]
    assert kill_kaydi == [], "birim durduysa pid'e sinyal atmak pid-yeniden-kullanım riskidir"
    assert (sb / "STOP").exists(), "işbirlikçi durdurma bayrağı her yolda yazılır"
    assert store.read_json(sprint.STATUS_FILE, {})["phase"] == "stopping"


def test_stop_birim_durdurulamazsa_pid_YEDEGINE_duser_ve_KAYDA_GECER(ortam, kill_kaydi, monkeypatch):
    monkeypatch.setenv("SAHTE_STOP_RC", "1")
    _durum_yaz(ortam.state, yol="systemd")
    sprint.stop()
    assert kill_kaydi == [(999999, 15)], "yedek durdurma denenmedi"
    olay = ortam.olaylar("sprint_systemd_durdurulamadi")
    assert olay and olay[-1]["birim"] == "meridian-sprint@20260813-151752.service"


def test_stop_popen_yolunda_pid_sinyaliyle_calisir(ortam, kill_kaydi):
    """Eski yol BİREBİR korunur — düzeltme 'her şeyi systemd'ye bağla' değildir."""
    sb = _durum_yaz(ortam.state, yol="popen")
    res = sprint.stop()
    assert res["stopping"] and kill_kaydi == [(999999, 15)]
    assert [s for s in ortam.systemctl_satirlari() if s.startswith("stop ")] == []
    assert (sb / "STOP").exists()

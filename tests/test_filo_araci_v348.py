"""FİLO ARACI — A1 bot filosunun ssh kalıpları TEK komut-satırı sözleşmesinde — v348 (2026-08-31)

NEDEN VAR. Bugüne kadar üç botun (`@sef`/`@bekci`/`@karne`) canlı durumu, journal kesiti, oturum
defteri ve profil güncellemesi Rol-1'in ELLE kurduğu ssh satırlarıyla okunuyordu. Elle kurulan
satır üç ölçülmüş tuzağı her seferinde yeniden açıyor:

  (1) SAHTE BAŞARI — `hermes profile update <ad>` etkileşimli onay ister. Boş stdin'de
      "Update cancelled" basar ve **RC=0 ile döner**. RC'ye bakan operatör güncellemenin
      YAPILDIĞINI sanır; canlı profil eski kalır ve bunu hiçbir sayaç göstermez.
  (2) UZAK SUDO — `sudo systemctl start` bu oturumların izin sınıfında ENGELLİ. Aracın onu
      "denemesi" bir arıza değil, bir SESSİZLİK üretir; doğru davranış KOŞMAMAK ve operatörün
      koşacağı tek bloğu BASMAKTIR.
  (3) BOT→BİRİM EŞLEMESİ — `sef` botunun birimi `meridian-sef` DEĞİL `meridian-brifing`tir.
      Elle yazılan her satır bu eşlemeyi yeniden hatırlamak zorundadır.

ÇİVİLERİN ÖLÇTÜĞÜ ŞEY: **kurulan komut dizgesi**. Alt-süreç MOCK'LANMAZ ve gerçek ssh testte
ÇAĞRILMAZ — araç, dizgeyi kuran SAF fonksiyonlar + onları koşan İNCE bir kabuk olarak
yapılanmıştır. "ssh'a hiç gidilmediği" iddiası da ölçülür ve bu ölçüm BOŞ DEĞİLDİR: PATH'e
gerçek bir `ssh` nişancısı konur, önce onun GERÇEKTEN ötebildiği gösterilir (pozitif kontrol),
sonra hiç ötmediği çivilenir.

SÖZLEŞME KOMUT SATIRIDIR (vaka 2026-08-30): `main()` değil, betiğin KENDİSİ koşulur; çıkış
kodları beyanlıdır (0 başarı · 1 doğrulama-kırmızısı · 2 kullanım hatası).
"""
from __future__ import annotations

import ast
import os
import pathlib
import re
import subprocess
import sys

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/filo.py"

from tests.conftest import betikten_modul_yukle  # noqa: E402


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    return betikten_modul_yukle(BETIK, "filo")


def _kod_satirlari() -> str:
    """Betiğin KODU: `#` yorumları ve DOCSTRING'leri düşülmüş hâli.

    Docstring'i AST ile düşürmek şart: bir tuzağı ANLATAN belge, tuzağı ARAYAN çiviye
    yakalanırsa çivi belgeyi cezalandırır (ölçüldü — bu dosyanın ilk koşumu). Kalan dize
    literalleri DÜŞÜRÜLMEZ: kurulan komutlar tam olarak orada yaşar."""
    kaynak = BETIK.read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    ds_satirlari: set[int] = set()
    for d in ast.walk(agac):
        if isinstance(d, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            g = d.body[0] if d.body else None
            if (isinstance(g, ast.Expr) and isinstance(g.value, ast.Constant)
                    and isinstance(g.value.value, str)):
                ds_satirlari.update(range(g.lineno, (g.end_lineno or g.lineno) + 1))
    return "\n".join(s for i, s in enumerate(kaynak.splitlines(), 1)
                     if i not in ds_satirlari and not s.lstrip().startswith("#"))


def _cli(*bayrak: str, ort: dict | None = None) -> subprocess.CompletedProcess:
    """GİRİŞ NOKTASI: `main([...])` değil, betiğin KENDİSİ. argparse `sys.argv`yi görmüyorsa
    (ölçülmüş `--uygula` sessiz-yok-sayma vakası) bu çağrı yakalar."""
    return subprocess.run([sys.executable, str(BETIK), *bayrak],
                          capture_output=True, text=True,
                          env={**os.environ, **(ort or {})})


# ═══════════════════════════════════════════════════════════════════════════
#  A. KOMUT-SATIRI SÖZLEŞMESİ
# ═══════════════════════════════════════════════════════════════════════════

def test_a1_YARDIM_BES_ALT_KOMUTU_ADIYLA_GOSTERIR():
    r = _cli("--help")
    assert r.returncode == 0, f"--help düştü: {r.returncode}\n{r.stderr}"
    for komut in ("durum", "journal", "oturumlar", "test-atesle", "profil-guncelle"):
        assert komut in r.stdout, f"`{komut}` --help metninde YOK:\n{r.stdout}"


def test_a2_CIKIS_KODLARI_YARDIMDA_BEYANLI():
    """Beyansız çıkış kodu sözleşme değildir: operatör 1'i 'çöktü' sanar."""
    r = _cli("--help")
    metin = r.stdout
    for beyan in ("0", "1", "2"):
        assert f"{beyan}=" in metin.replace(" = ", "=").replace(" =", "="), (
            f"çıkış kodu {beyan} --help'te beyan edilmiyor:\n{metin}")


def test_a3_TANIMSIZ_ALT_KOMUT_KULLANIM_HATASI_2():
    r = _cli("boyle-bir-komut-yok")
    assert r.returncode == 2, f"beklenen 2, gelen {r.returncode}\n{r.stdout}{r.stderr}"


def test_a4_TANIMSIZ_BOT_KULLANIM_HATASI_2():
    """Bot adı ROSTER'dan gelir; tanımsız ad ssh'a HİÇ ulaşmamalı."""
    r = _cli("journal", "olmayan-bot")
    assert r.returncode == 2, f"beklenen 2, gelen {r.returncode}\n{r.stdout}{r.stderr}"


@pytest.mark.parametrize("komut", ["durum", "journal", "oturumlar", "test-atesle",
                                   "profil-guncelle"])
def test_a5_HER_ALT_KOMUTUN_KENDI_YARDIMI_VAR(komut):
    r = _cli(komut, "--help")
    assert r.returncode == 0, f"{komut} --help düştü:\n{r.stderr}"
    assert len(r.stdout.strip()) > 40, f"{komut} --help boş sayılır:\n{r.stdout}"


@pytest.mark.parametrize("komut,deger", [("journal", "0"), ("journal", "-3"),
                                         ("oturumlar", "0"), ("oturumlar", "-1")])
def test_a6_GECERSIZ_N_KULLANIM_HATASI_2_HAM_TRACEBACK_DEGIL(komut, deger, tmp_path):
    """BEYAN EDİLEN SÖZLEŞME: 2=kullanım hatası. Ham `ValueError` traceback'i + exit 1,
    operatöre "araç çöktü" der — oysa ölçülen şey KULLANICININ yazdığı değerdir.

    Nişancı PATH'i BİLEREK kuruluyor: doğrulama kalkarsa çağrı GEÇERLİ bir komut kurup ssh'a
    giderdi. Nişancı hem o sızıntıyı çiviler hem de mutasyon turunun canlıya dokunmasını önler.
    """
    ort, iz = _nisanci(tmp_path)
    r = _cli(komut, "bekci", "-n", deger, ort=ort)
    assert not iz.exists(), f"geçersiz `-n` ssh'a KADAR gitti: {iz.read_text('utf-8')!r}"
    assert r.returncode == 2, f"beklenen 2, gelen {r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "Traceback" not in r.stderr, f"ham traceback sızdı:\n{r.stderr}"
    assert "-n" in r.stderr or "satır" in r.stderr, (
        f"hata mesajı HANGİ bayrağın hatalı olduğunu söylemiyor:\n{r.stderr}")


# ═══════════════════════════════════════════════════════════════════════════
#  B. ROSTER VE BOT→BİRİM EŞLEMESİ — TÜRETİLİR, YAZILMAZ
# ═══════════════════════════════════════════════════════════════════════════

def test_b1_ROSTER_PROFIL_DIZINLERINDEN_TURER():
    """TEK-KAYNAK YASASI: kod içine yazılmış bir bot demeti canlıyla sessizce ayrışır."""
    mod = _yukle()
    diskteki = sorted(p.name for p in (KOK / "deploy/hermes/profiles").iterdir() if p.is_dir())
    assert mod.botlar() == diskteki, f"roster diskle ayrıştı: {mod.botlar()} != {diskteki}"
    assert len(diskteki) >= 3, "roster kaynağı bayat (üç bot bekleniyordu)"


def test_b2_BOT_ADLARI_KAYNAKTA_LITERAL_OLARAK_GECMEZ():
    """Ayrışma çivisi: `botlar()` türetse bile başka bir yerde sabitlenmiş bir liste
    ikinci gerçeği geri getirirdi."""
    kod = _kod_satirlari()
    for ad in ("bekci", "karne", "sef"):
        assert f'"{ad}"' not in kod and f"'{ad}'" not in kod, (
            f"`{ad}` kaynakta dize literali olarak geçiyor — roster/eşleme türetilmiyor")


def test_b3_SEF_BOTUNUN_BIRIMI_MERIDIAN_BRIFING():
    """TUZAK ÇİVİSİ: ad benzerliğinden `meridian-sef` uydurmak canlıda 'Unit not found' verir.
    Eşleme birim dosyalarının KENDİ `Environment=HERMES_HOME=` satırından ÖLÇÜLÜR."""
    mod = _yukle()
    p = mod.profiller()
    assert "sef" in p, f"sef eşlemesi bulunamadı: {sorted(p)}"
    assert p["sef"]["birim"] == "meridian-brifing.service", p["sef"]
    assert p["bekci"]["birim"] == "meridian-bekci.service", p["bekci"]
    assert p["karne"]["birim"] == "meridian-karne.service", p["karne"]


def test_b4_TIMER_VE_UZAK_EV_DE_TURETILIR():
    mod = _yukle()
    p = mod.profiller()
    assert p["bekci"]["timer"] == "meridian-bekci.timer", p["bekci"]
    assert p["sef"]["timer"] == "meridian-brifing.timer", p["sef"]
    assert p["karne"]["ev"] == "/home/ubuntu/.hermes/profiles/karne", p["karne"]


# ═══════════════════════════════════════════════════════════════════════════
#  C. SSH SARMALI — KİMLİK VE GEÇERSİZ KILMA
# ═══════════════════════════════════════════════════════════════════════════

def test_c1_SSH_SARMALI_ANAHTAR_VE_HOST_TASIR():
    mod = _yukle()
    argv = mod.ssh_sarmali("echo merhaba")
    assert argv[0] == "ssh"
    assert "-i" in argv, argv
    assert argv[argv.index("-i") + 1].endswith("oci-a1.key"), argv
    assert mod.varsayilan_host() in argv, argv
    assert argv[-1] == "echo merhaba", argv


def test_c4_KIMLIK_UC_KATMANLI_CLI_ENV_SABIT():
    """A1 kimliği bu depoda ZATEN iki betikte ortam değişkeninden okunuyor
    (`ops/pull-a1-backups.sh`, `ops/state_yetim_temizle.sh`). Aynı adları okumayan bir araç
    ÜÇÜNCÜ bir gerçek yaratır: A1 taşındığında iki betik taşınır, bu araç sessizce eskiye gider.

    Öncelik: CLI bayrağı > ortam değişkeni > sabit varsayılan.
    """
    mod = _yukle()
    # 1) env adları UYDURULMADI — kardeş betiklerde GERÇEKTEN var
    for betik, ad in ((KOK / "ops/pull-a1-backups.sh", mod.ENV_IP),
                      (KOK / "ops/state_yetim_temizle.sh", mod.ENV_ANAHTAR)):
        assert ad in betik.read_text(encoding="utf-8"), f"{ad} {betik.name} içinde YOK"

    ort = {mod.ENV_KULLANICI: "root", mod.ENV_IP: "10.1.2.3", mod.ENV_ANAHTAR: "/tmp/env.key"}
    # 2) env kurulunca kurulan komut ONU kullanır
    r = _cli("durum", "--komut-yaz", ort=ort)
    assert r.returncode == 0, r.stderr
    assert "root@10.1.2.3" in r.stdout, r.stdout
    assert "/tmp/env.key" in r.stdout, r.stdout
    # 3) CLI bayrağı env'i EZER
    r2 = _cli("durum", "--komut-yaz", "--host", "ubuntu@9.9.9.9", "--anahtar", "/tmp/cli.key",
              ort=ort)
    assert "ubuntu@9.9.9.9" in r2.stdout and "/tmp/cli.key" in r2.stdout, r2.stdout
    assert "10.1.2.3" not in r2.stdout and "/tmp/env.key" not in r2.stdout, r2.stdout


def test_c2_ANAHTARDA_TILDE_GENISLETILIR():
    """`ssh -i ~/...` argv'de tilde'yi KENDİ genişletmez; genişletmeyen araç 'no such
    identity' alır ve parola sorar (etkileşimsiz koşumda asılır)."""
    mod = _yukle()
    argv = mod.ssh_sarmali("x")
    assert "~" not in argv[argv.index("-i") + 1], argv


def test_c3_HOST_VE_ANAHTAR_CLI_DAN_GECERSIZ_KILINIR():
    r = _cli("durum", "--komut-yaz", "--host", "ubuntu@10.0.0.9", "--anahtar", "/tmp/k.key")
    assert r.returncode == 0, r.stderr
    assert "ubuntu@10.0.0.9" in r.stdout, r.stdout
    assert "/tmp/k.key" in r.stdout, r.stdout


# ═══════════════════════════════════════════════════════════════════════════
#  D. `durum` — SALT-OKUMA, SUDO'SUZ, ÜÇ ALANI BİRDEN SORAR
# ═══════════════════════════════════════════════════════════════════════════

def test_d1_DURUM_KOMUTU_SUDOSUZ_VE_UC_ALANI_SORAR():
    mod = _yukle()
    k = mod.durum_komutu(mod.durum_birimleri())
    assert "sudo" not in k, f"`durum` salt-okuma olmalı:\n{k}"
    assert "systemctl show" in k
    for alan in ("ActiveState", "Result", "ExecMainStatus"):
        assert f"-p {alan}" in k, f"{alan} sorulmuyor:\n{k}"


def test_d2_DURUM_ALTI_BIRIMI_KAPSAR():
    mod = _yukle()
    birimler = [b for _, b in mod.durum_birimleri()]
    for b in ("meridian-brifing.service", "meridian-bekci.service", "meridian-karne.service",
              "meridian-brifing.timer", "meridian-bekci.timer", "meridian-karne.timer"):
        assert b in birimler, f"{b} kapsam dışı: {birimler}"


SENTETIK_YESIL = """@@BIRIM meridian-bekci.service
ActiveState=inactive
SubState=dead
Result=success
ExecMainStatus=0
ExecMainExitTimestamp=Sun 2026-08-31 09:29:41 UTC
@@BIRIM meridian-bekci.timer
ActiveState=active
SubState=waiting
Result=success
NextElapseUSecRealtime=Mon 2026-09-01 10:01:00 UTC
"""


def test_d3_AYRISTIRICI_GERCEK_BICIMI_OKUR():
    mod = _yukle()
    o = mod.durum_ayristir(SENTETIK_YESIL)
    assert o["meridian-bekci.service"]["Result"] == "success"
    assert o["meridian-bekci.service"]["ExecMainStatus"] == "0"
    assert o["meridian-bekci.timer"]["ActiveState"] == "active"


def test_d4_OLCULEMEYEN_ALAN_SIFIR_DEGIL_NONE():
    """UYDURMA YASAĞI: timer'ın `ExecMainStatus`ı yoktur; onu 0 saymak 'başarılı koştu' der."""
    mod = _yukle()
    o = mod.durum_ayristir(SENTETIK_YESIL)
    assert o["meridian-bekci.timer"].get("ExecMainStatus") is None


def test_d5_HUKUM_YESILDE_0_KIRMIZIDA_1():
    mod = _yukle()
    kayit = [("bekci", "meridian-bekci.service"), ("bekci", "meridian-bekci.timer")]
    rc, sorun = mod.durum_hukmu(kayit, mod.durum_ayristir(SENTETIK_YESIL))
    assert (rc, sorun) == (0, []), sorun
    kirmizi = SENTETIK_YESIL.replace("Result=success\nExecMainStatus=0",
                                     "Result=exit-code\nExecMainStatus=1")
    rc2, sorun2 = mod.durum_hukmu(kayit, mod.durum_ayristir(kirmizi))
    assert rc2 == 1, "kırmızı birim hükmü geçti"
    assert any("exit-code" in s or "ExecMainStatus" in s for s in sorun2), sorun2


def test_d6_OLCULEMEYEN_BIRIM_SESSIZCE_YESIL_SAYILMAZ():
    mod = _yukle()
    kayit = [("bekci", "meridian-bekci.service")]
    rc, sorun = mod.durum_hukmu(kayit, {})
    assert rc == 1 and sorun, "systemctl hiç konuşmadıysa hüküm YEŞİL OLAMAZ"
    assert "ÖLÇÜLEMEDİ" in " ".join(sorun), sorun


def test_d7_BOS_DAMGA_KOR_NOKTAYI_ADIYLA_SOYLER():
    """ÖLÇÜLEN VAKA (A1, 2026-08-31 13:24 reboot): birim 09:29'da koştu, systemd damgası BOŞ.
    O satırda `Result=success` + `ExecMainStatus=0` HİÇ KOŞMAMIŞ birimde de görünür — tablo
    'koştu' DEMEZ ve bunu söylemeyen tablo operatörü yanıltır."""
    mod = _yukle()
    kayit = [("bekci", "meridian-bekci.service"), ("bekci", "meridian-bekci.timer")]
    damgasiz = mod.durum_ayristir(
        "@@BIRIM meridian-bekci.service\nActiveState=inactive\nResult=success\n"
        "ExecMainStatus=0\n@@BIRIM meridian-bekci.timer\nActiveState=active\n")
    not_ = mod.damga_notu(kayit, damgasiz)
    assert not_ and "journal" in not_, f"kör nokta sessiz kaldı: {not_!r}"
    assert "meridian-bekci.service" in not_, not_
    # Ters yön: damga VARSA not BASILMAZ (yoksa not gürültüye döner ve okunmaz olur)
    assert mod.damga_notu(kayit, mod.durum_ayristir(SENTETIK_YESIL)) is None


def test_d8_NOT_GERCEK_KOSUMDA_BASILIR(tmp_path):
    """YASA 6 — okuyucusuz yazım yok: not hesaplanıp basılmazsa üretilmemişten farksızdır.

    Bu çivi DİZGE VARLIĞI ölçmez (ilk hâli öyleydi ve mutasyon `damga_notu(kayit, olculen)`
    satırını basmadan bırakınca YEŞİL kaldı — yanlış sebeple yeşil). Burada CLI GERÇEKTEN
    koşulur: PATH'e `systemctl show` çıktısını taklit eden GERÇEK bir `ssh` betiği konur
    (mock değil, ayrı süreç) ve not'un STDOUT'a düştüğü ölçülür.
    """
    mod = _yukle()
    bloklar = []
    for _, birim in mod.durum_birimleri():
        if birim.endswith(".timer"):
            bloklar += [f"{mod.AYRAC} {birim}", "ActiveState=active", "SubState=waiting"]
        else:
            # DAMGASIZ servis — ölçülen A1 reboot vakasının birebir şekli
            bloklar += [f"{mod.AYRAC} {birim}", "ActiveState=inactive", "SubState=dead",
                        "Result=success", "ExecMainStatus=0"]
    kutu = tmp_path / "bin"
    kutu.mkdir()
    sh = kutu / "ssh"
    # `printf` KABUK YERLEŞİĞİDİR: PATH'te yalnız bu kutu var, dışarıdan `cat` çözülemezdi
    # (ölçüldü — çivinin ilk hâli tam bu yüzden kırmızıydı).
    assert not any("'" in s for s in bloklar), "sentetik blokta tek tırnak sarmalı bölerdi"
    arg = " ".join(f"'{s}'" for s in bloklar)
    sh.write_text(f"#!/bin/sh\nprintf '%s\\n' {arg}\n", encoding="utf-8")
    sh.chmod(0o755)

    r = _cli("durum", ort={"PATH": str(kutu)})
    assert r.returncode == 0, f"sentetik yeşil tabloda hüküm kırmızı:\n{r.stdout}\n{r.stderr}"
    assert "NOT —" in r.stdout and "journal" in r.stdout, (
        f"damga kör noktası STDOUT'a HİÇ düşmedi — not okuyucusuz:\n{r.stdout}")


def test_d9_TIMERI_OLMAYAN_SERVIS_TABLODAN_DUSMEZ():
    """SESSİZLİK-BİLGİYE EMSALİ: servisi olup timer'ı olmayan bot, kadansı HİÇ açılmamış bir
    bottur ve onun sessizliği 'boşken sessiz' davranışından AYIRT EDİLEMEZ. Eski hâlde bu satır
    tablodan sessizce düşüyordu — yani en tehlikeli hâl, en görünmez hâldi."""
    mod = _yukle()
    sentetik = {"zzz": {"birim": "meridian-zzz.service", "timer": None,
                        "timer_beklenen": "meridian-zzz.timer",
                        "kok": "/home/ubuntu/.hermes/profiles",
                        "ev": "/home/ubuntu/.hermes/profiles/zzz"}}
    eksik = mod.eksik_timerlar(sentetik)
    assert eksik == [("zzz", "meridian-zzz.timer")], eksik
    # Ters yön: bugünkü repoda üç timer da VAR — çivi boş yere ötmemeli
    assert mod.eksik_timerlar() == [], mod.eksik_timerlar()

    rc, metin = mod.durum_raporu([("bekci", "meridian-bekci.service")],
                                 mod.durum_ayristir(SENTETIK_YESIL), eksik)
    assert rc == 1, f"eksik timer hükmü YEŞİL kaldı:\n{metin}"
    assert "meridian-zzz.timer" in metin, f"eksik timer TABLODA yok:\n{metin}"
    assert "BİRİM YOK" in metin, f"eksik timer satırı sebebini söylemiyor:\n{metin}"
    # KIRMIZI olmak yetmez: hüküm NEDENİ ADIYLA saymalı. Sebepsiz bir kırmızı, operatörü
    # tablonun tamamını gözle taramaya zorlar — (a) mutasyonunun öğrettiği ders.
    gerekce = metin.split("HÜKÜM: KIRMIZI", 1)[1]
    assert "meridian-zzz.timer" in gerekce, (
        f"hüküm KIRMIZI ama gerekçe listesinde eksik timer'ın ADI yok:\n{gerekce}")


# ═══════════════════════════════════════════════════════════════════════════
#  E. `journal`
# ═══════════════════════════════════════════════════════════════════════════

def test_e1_JOURNAL_KOMUTU_BIRIMI_VE_N_TASIR():
    mod = _yukle()
    k = mod.journal_komutu("bekci", 40)
    assert "journalctl -u meridian-bekci.service" in k, k
    assert "-n 40" in k, k
    assert "--no-pager" in k, k
    assert "sudo" not in k, k


def test_e2_JOURNAL_GREP_Q_ILE_BORULANMAZ():
    """ÖLÇÜLMÜŞ TUZAK (2026-08-23): `grep -q` eşleşince boruyu erken kapatır, journalctl
    SIGPIPE ile ölür ve çıktı YARIM gelir."""
    mod = _yukle()
    kurulanlar = [mod.journal_komutu("bekci", 40), mod.kanit_komutu("bekci"),
                  mod.durum_komutu(mod.durum_birimleri()),
                  mod.profil_guncelle_komutu("bekci"), mod.oturumlar_komutu("bekci", 5)]
    for k in kurulanlar:
        assert "grep -q" not in k, f"kurulan komutta `grep -q`:\n{k}"
    assert "grep -q" not in _kod_satirlari(), (
        "kaynak KODUNDA `grep -q` var — journalctl borusunu kesebilir")


# ═══════════════════════════════════════════════════════════════════════════
#  F. `oturumlar` — SALT-OKUMA SQLITE, UZAK TIRNAK GÜVENLİĞİ
# ═══════════════════════════════════════════════════════════════════════════

def test_f1_PROGRAM_SALT_OKUMA_URI_KULLANIR():
    """Canlı hermes bu deftere YAZAR. Yazılabilir açılış, botun kendi oturumunu kilitleyebilir
    ve `-wal` dosyasını aracın adına büyütür."""
    mod = _yukle()
    p = mod.oturumlar_programi("bekci", 10)
    assert "mode=ro" in p, p
    assert "uri=True" in p, p


def test_f2_PROGRAM_DOGRU_DEFTERI_VE_SEMAYI_OKUR():
    mod = _yukle()
    p = mod.oturumlar_programi("karne", 7)
    assert "/home/ubuntu/.hermes/profiles/karne/state.db" in p, p
    assert "FROM sessions" in p, p
    assert "LIMIT 7" in p, p


def test_f3_PROGRAMDA_TEK_TIRNAK_YOK():
    """UZAK TIRNAK ÇİVİSİ: program uzak kabuğa `python3 -c '<program>'` olarak gider. İçindeki
    tek bir `'` sarmalı sessizce böler ve komut BAŞKA bir şey çalıştırır."""
    mod = _yukle()
    p = mod.oturumlar_programi("sef", 5)
    assert "'" not in p, f"programda tek tırnak var — uzak sarmalı bölünür:\n{p}"
    k = mod.oturumlar_komutu("sef", 5)
    assert k.startswith("python3 -c '") and k.endswith("'"), k


def test_f5_UZAK_PROGRAM_SALT_ASCII():
    """Uzak `python3` C-locale altında koşabilir; ASCII dışı bir `print` orada
    `UnicodeEncodeError` ile ölür — ve o ölüm YEREL çıktıda 'boş sonuç' gibi görünür."""
    mod = _yukle()
    for p in (mod.oturumlar_programi("bekci", 3), mod.kanit_komutu("bekci")):
        p.encode("ascii")  # ASCII dışı karakter varsa UnicodeEncodeError


def test_f4_N_TAMSAYIYA_ZORLANIR():
    """Enjeksiyon yüzeyi: `n` uzak programa GÖMÜLÜR."""
    mod = _yukle()
    with pytest.raises((ValueError, TypeError)):
        mod.oturumlar_programi("sef", "5; DROP")


# ═══════════════════════════════════════════════════════════════════════════
#  G. `test-atesle` — KOŞMAZ, BASAR
# ═══════════════════════════════════════════════════════════════════════════

def test_g1_BLOK_SUDOLU_SATIRI_VE_KOSULMADI_UYARISINI_TASIR():
    mod = _yukle()
    blok = mod.test_atesle_blogu("bekci")
    assert "sudo systemctl start meridian-bekci.service" in blok, blok
    assert "KOŞULMADI" in blok, "operatör bloğu koşulmuş sanabilir"
    assert "--kanit" in blok, "koşum sonrası adım gösterilmiyor"


def test_g2_CLI_BLOGU_BASAR_VE_0_DONER():
    r = _cli("test-atesle", "bekci")
    assert r.returncode == 0, f"{r.returncode}\n{r.stderr}"
    assert "sudo systemctl start meridian-bekci.service" in r.stdout, r.stdout


def test_g3_KANIT_ADIMI_SALT_OKUMADIR():
    """`--kanit` KOŞAR ama yalnız okur: içinde `sudo`/`start`/`restart` GEÇEMEZ."""
    mod = _yukle()
    k = mod.kanit_komutu("bekci")
    assert "sudo" not in k, k
    assert "systemctl start" not in k and "systemctl restart" not in k, k
    assert "systemctl show" in k and "-p Result" in k and "-p ExecMainStatus" in k, k
    assert "journalctl -u meridian-bekci.service" in k, k
    assert "mode=ro" in k, "kanıt turu state.db son oturumunu okumuyor"


def test_g4_KANIT_HUKMU_BASARISIZ_KOSUMU_KIRMIZI_YAPAR():
    mod = _yukle()
    yesil = "@@BIRIM meridian-bekci.service\nResult=success\nExecMainStatus=0\n"
    rc, _ = mod.durum_hukmu([("bekci", "meridian-bekci.service")], mod.durum_ayristir(yesil))
    assert rc == 0
    kirmizi = yesil.replace("success", "exit-code").replace("ExecMainStatus=0",
                                                            "ExecMainStatus=1")
    rc2, sorun = mod.durum_hukmu([("bekci", "meridian-bekci.service")],
                                 mod.durum_ayristir(kirmizi))
    assert rc2 == 1 and sorun


# ═══════════════════════════════════════════════════════════════════════════
#  H. `profil-guncelle` — SAHTE BAŞARI TUZAĞI
# ═══════════════════════════════════════════════════════════════════════════

def test_h1_IPTAL_CIKTISI_RC_SIFIR_OLSA_DA_KIRMIZI():
    """ASIL ÇİVİ. Ölçülmüş davranış: boş stdin → "Update cancelled" + **RC=0**."""
    mod = _yukle()
    ok, neden = mod.guncelleme_hukmu("Update cancelled by user.\n", 0)
    assert ok is False, "RC=0 SAHTE BAŞARIYI geçirdi"
    assert "SAHTE BAŞARI" in neden.upper() or "İPTAL" in neden.upper(), (
        f"hüküm kırmızı ama NEDENİ iptali ADIYLA söylemiyor — teşhis kayboldu: {neden!r}")


def test_h2_BASARI_DIZGESI_YOKSA_KIRMIZI():
    mod = _yukle()
    ok, neden = mod.guncelleme_hukmu("some unrelated chatter\n", 0)
    assert ok is False and neden


def _yesil_cikti(mod) -> str:
    """Bir güncellemenin YEŞİL sayılması için gereken TÜM tanıklar. Yedek işareti bu kümenin
    parçasıdır (düzeltme turu 2): yedeksiz bir güncelleme geri alınamaz."""
    return f"{mod.TAR_ISARETI}\n{mod.BASARI_DIZGESI} profile\n"


def test_h3_BASARI_DIZGESI_VARSA_VE_RC_SIFIRSA_YESIL():
    mod = _yukle()
    ok, _ = mod.guncelleme_hukmu(_yesil_cikti(mod), 0)
    assert ok is True


def test_h4_RC_SIFIR_DEGILSE_DIZGE_VARSA_DA_KIRMIZI():
    mod = _yukle()
    ok, neden = mod.guncelleme_hukmu(_yesil_cikti(mod), 3)
    assert ok is False and "3" in neden, neden


def test_h10_YEDEK_ALINAMADIYSA_HUKUM_KIRMIZI():
    """Dal-sonu incelemesi Important-1: tar yedeği bir KAPI değil VAAT'ti. Yedeksiz bir
    güncelleme GERİ ALINAMAZ — o yüzden yedek, yeşil hükmün ŞARTIDIR.

    İki katman: (a) komut dizgesinde tar update'e `&&` ile BAĞLI (tar düşerse update hiç
    koşmaz), (b) hüküm yedek işaretini ARAR ve yokluğunu ADIYLA söyler.
    """
    mod = _yukle()
    # (a) KOMUT DİZGESİ: tar ile update arasında `&&` var, `;` YOK
    k = mod.profil_guncelle_komutu("bekci")
    ara = k[k.index("tar "):k.index("hermes profile update")]
    assert "&&" in ara, f"tar update'e bağlı değil — düşse de update koşar:\n{ara}"
    assert ";" not in ara, f"tar ile update arasında `;` var — bağ KOPUK:\n{ara}"

    # (b) HÜKÜM: yedek işareti yoksa kırmızı VE gerekçe yedeği adıyla anıyor
    tarsiz = f"tar: Cannot open: Permission denied\n{mod.RC_ISARETI} 2\n"
    ok, neden = mod.guncelleme_hukmu(tarsiz, 2)
    assert ok is False, "yedeksiz güncelleme YEŞİL geçti"
    assert "yedek" in neden.lower(), (
        f"hüküm kırmızı ama gerekçe yedeği ADIYLA söylemiyor — teşhis kayboldu: {neden!r}")
    # Ters yön: yedek işareti VARSA bu gerekçe ÖTMEZ
    ok2, _ = mod.guncelleme_hukmu(_yesil_cikti(mod), 0)
    assert ok2 is True


def test_h11_MODEL_KIYASI_ESITLIK_ALT_DIZGE_DEGIL():
    """Dal-sonu incelemesi Important-2: `beklenen in canli` ÖNEK vakasında sahte-aynılık verir.
    `opus-4-1` beklenirken canlı `opus-4-1-ultra` ise alt-dizge kıyası 'AYNI' der — ve bu tam
    da bugünkü Ultra-geçişinin sınıfıdır (aynı ad, uzatılmış sürüm)."""
    mod = _yukle()
    blok = "115:  default: opus-4-1-ultra\n116:  max_tokens: 8000\n"
    canli = mod.canli_model_varsayilani(blok)
    assert canli == "opus-4-1-ultra", canli
    assert canli != "opus-4-1", "önek EŞİT sayıldı — sahte aynılık"
    # Ölçülemeyen blok `None` döner; "aynı" DEMEZ (uydurma yasağı)
    assert mod.canli_model_varsayilani("hiç default satırı yok\n") is None


def test_h9_UYGULA_ILE_KOMUT_YAZ_ONIZLEMEDIR_KOSUM_DEGIL(tmp_path):
    """KRİTİK (inceleme, düzeltme turu 1). `--uygula` dalı `_ssh_kos`u ATLAYIP `_kos`u doğrudan
    çağırıyordu: `--komut-yaz` BU DALDA sessizce yok sayılıyor, yani önizleme bekleyen operatör
    CANLI PROFİLİ DEĞİŞTİRİYORDU.

    Bu, 18-çivi vakasının TERS YÖNLÜ tekrarıdır: orada etkisiz olan GÜVENLİ bayraktı, burada
    etkisiz olan GÜVENLİK bayrağı — ve o yön daha tehlikelidir. Çivi davranışla ölçer: PATH'e
    iz bırakan gerçek bir `ssh` konur, komutun STDOUT'a BASILDIĞI ve ssh'a HİÇ GİDİLMEDİĞİ
    aynı koşumda görülür.
    """
    ort, iz = _nisanci(tmp_path)
    r = _cli("profil-guncelle", "bekci", "--uygula", "--komut-yaz", ort=ort)
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert not iz.exists(), (
        "`--uygula --komut-yaz` GERÇEKTEN ssh çalıştırdı — güvenlik bayrağı etkisiz: "
        f"{iz.read_text(encoding='utf-8')!r}")
    assert "hermes profile update bekci --force-config" in r.stdout, (
        f"önizleme istendi ama komut BASILMADI:\n{r.stdout}")
    assert r.stdout.lstrip().startswith("ssh "), (
        f"basılan şey koşulabilir bir ssh satırı değil:\n{r.stdout}")


def test_h8_UZAK_RC_OLCULEMEDIGINDE_SIFIR_VARSAYILMAZ():
    """ssh'ın kendi RC'si bu zincirde HEP 0'dır (son halka `echo`). Gerçek RC `@@RC`
    işaretinden okunur; işaret yoksa cevap `None`dır — 0 varsaymak sahte başarıdır."""
    mod = _yukle()
    assert mod.uzak_rc(f"{mod.RC_ISARETI} 3\n") == 3
    assert mod.uzak_rc("hiç işaret yok\n") is None
    assert mod.uzak_rc(f"{mod.RC_ISARETI} anlamsiz\n") is None
    ok, neden = mod.guncelleme_hukmu(_yesil_cikti(mod), None)
    assert ok is False and "ÖLÇÜLEMEDİ" in neden, neden


def _guncelleme_shim(tmp_path, mod, canli_model: str):
    """PATH'e GERÇEK bir `ssh` koyar; tam bir başarılı güncelleme çıktısını taklit eder.
    Mock DEĞİL — ayrı süreç. Gerçek ssh'a hiçbir koşulda gidilmez."""
    satirlar = [mod.TAR_ISARETI, f"{mod.BASARI_DIZGESI} profile", f"{mod.RC_ISARETI} 0",
                mod.DOGRULAMA_ISARETI, f"115:  default: {canli_model}",
                "116:  max_tokens: 8000"]
    assert not any("'" in s for s in satirlar), satirlar
    kutu = tmp_path / "bin"
    kutu.mkdir()
    sh = kutu / "ssh"
    sh.write_text("#!/bin/sh\nprintf '%s\\n' " + " ".join(f"'{s}'" for s in satirlar) + "\n",
                  encoding="utf-8")
    sh.chmod(0o755)
    return {"PATH": str(kutu)}


def test_h12_ONEK_MODEL_CANLI_YOLDA_AYRISMA_SAYILIR(tmp_path):
    """CLI YOLU (saf fonksiyon değil): sahte-aynılık burada operatöre ulaşırdı."""
    mod = _yukle()
    beklenen = mod.repo_model_varsayilani("bekci")
    assert beklenen, "repo model.default okunamadı — çivi ölçüm YAPAMAZ"

    ort = _guncelleme_shim(tmp_path, mod, f"{beklenen}-ek")
    r = _cli("profil-guncelle", "bekci", "--uygula", ort=ort)
    assert r.returncode == 1, f"önek AYNI sayıldı — sahte aynılık:\n{r.stdout}"
    assert "AYRIŞTI" in r.stdout, r.stdout

    esit_kok = tmp_path / "esit"
    esit_kok.mkdir()
    r2 = _cli("profil-guncelle", "bekci", "--uygula",
              ort=_guncelleme_shim(esit_kok, mod, beklenen))
    assert r2.returncode == 0, f"birebir EŞİT model kırmızı sayıldı:\n{r2.stdout}"
    assert "AYNI" in r2.stdout, r2.stdout


def test_h13_SQL_UCLUSU_API_ILE_AYRISMIYOR():
    """ÇAPRAZ ÇİVİ (tek-kaynak yasası, kaçınılmaz kopya). `meridian/api.py::_ajan_oturumlar`
    ile `ops/filo.py::oturumlar_programi` AYNI üçlüyü okur (kolonlar + ORDER BY). Araç
    `meridian` ithal EDEMEZ (obs kapısı), yani kopya zorunludur — ama ayrışması SESSİZ olamaz.

    `meridian` BURADA DA ithal edilmez: iki dosya METİN olarak okunur.
    """
    def _uclu(yol: pathlib.Path) -> tuple[str, str]:
        ham = yol.read_text(encoding="utf-8")
        # Bitişik dize literalleri birleştirilir (`"…"\n  f"…"`), yoksa SELECT ikiye bölünür
        duz = re.sub(r'"\s*\n\s*f?"', "", ham)
        m = re.search(r"SELECT\s+(.+?)\s+FROM sessions\s+ORDER BY\s+(.+?)\s+LIMIT", duz)
        assert m, f"{yol.name}: sessions SELECT'i bulunamadı — çivi bayat"
        kolon = ",".join(x.strip() for x in m.group(1).split(","))
        sira = ",".join(x.strip() for x in m.group(2).split(","))
        return kolon, sira

    api = _uclu(KOK / "meridian/api.py")
    filo = _uclu(BETIK)
    assert api == filo, (
        f"sessions sorgusu AYRIŞTI — api.py {api} vs filo.py {filo}. İki okuyucu aynı defteri "
        "farklı sıralarsa 'son oturum' iki yüzeyde FARKLI çıkar.")


def test_h5_BLOK_TAR_KOPYASI_ONAY_VE_FORCE_CONFIG_TASIR():
    mod = _yukle()
    k = mod.profil_guncelle_komutu("bekci")
    assert "tar" in k, k
    assert "printf" in k and "hermes profile update bekci --force-config" in k, k
    assert "config.yaml" in k, "doğrulama grep'i yok"


def test_h6_ONAY_BORUSU_ETKILESIMI_KAPATIR():
    """`printf y | ` OLMADAN komut boş stdin'de iptal eder — tuzağın kendisi."""
    mod = _yukle()
    k = mod.profil_guncelle_komutu("sef")
    onay = k.index("printf")
    guncelle = k.index("hermes profile update")
    assert onay < guncelle, f"onay borusu update'ten SONRA:\n{k}"
    assert "|" in k[onay:guncelle], f"printf update'e BORULANMIYOR:\n{k}"


def test_h7_CLI_UYGULAMASIZ_KURU_KALIR():
    """Bayraksız çağrı canlı profile DOKUNMAZ — bloğu basar."""
    r = _cli("profil-guncelle", "bekci")
    assert r.returncode == 0, r.stderr
    assert "hermes profile update bekci --force-config" in r.stdout
    assert "--uygula" in r.stdout, "koşum bayrağı gösterilmiyor"


# ═══════════════════════════════════════════════════════════════════════════
#  I. YAPISAL — meridian YOK, subprocess TEK YERDE
# ═══════════════════════════════════════════════════════════════════════════

def _ithaller(agac) -> set[str]:
    adlar = set()
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            adlar.update(a.name.split(".")[0] for a in d.names)
        elif isinstance(d, ast.ImportFrom) and d.module and d.level == 0:
            adlar.add(d.module.split(".")[0])
        elif isinstance(d, ast.ImportFrom) and d.level:
            adlar.add("<göreli>")
    return adlar


def test_i1_MERIDIAN_ITHAL_EDILMEZ():
    """`meridian` içe aktarılırsa `meridian.obs` erişilebilir olur ve bu araç pytest DIŞINDA,
    operatörün elinde koşar: canlı YEREL deftere yazardı (3 vaka, 2026-08-30)."""
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    ith = _ithaller(agac)
    assert "meridian" not in ith, f"meridian ithal ediliyor: {sorted(ith)}"
    assert "<göreli>" not in ith, f"göreli ithal var (paket bağı): {sorted(ith)}"


def test_i2_YALNIZ_STDLIB():
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    disarda = _ithaller(agac) - set(sys.stdlib_module_names)
    assert not disarda, f"stdlib dışı ithal: {sorted(disarda)}"


def test_i3_ALT_SUREC_TEK_KABUKTA():
    """Dizgeyi kuran fonksiyonlar SAF kalmalı: `subprocess.run` bir tek ince kabukta."""
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    kosanlar = set()
    for d in ast.walk(agac):
        if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for i in ast.walk(d):
                if (isinstance(i, ast.Call) and isinstance(i.func, ast.Attribute)
                        and i.func.attr == "run"
                        and isinstance(i.func.value, ast.Name)
                        and i.func.value.id == "subprocess"):
                    kosanlar.add(d.name)
    assert kosanlar == {"_kos"}, f"subprocess.run beklenmedik yerde: {sorted(kosanlar)}"


# ═══════════════════════════════════════════════════════════════════════════
#  J. SSH NİŞANCISI — "testte ssh'a gidilmedi" ÖLÇÜLÜR, İDDİA EDİLMEZ
# ═══════════════════════════════════════════════════════════════════════════

def _nisanci(tmp_path) -> tuple[dict, pathlib.Path]:
    """PATH'e GERÇEK bir `ssh` betiği koyar (mock değil: ayrı bir süreç). Çağrılırsa iz bırakır."""
    kutu = tmp_path / "bin"
    kutu.mkdir()
    iz = tmp_path / "ssh-cagrildi.iz"
    sh = kutu / "ssh"
    sh.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> {iz}\nexit 0\n', encoding="utf-8")
    sh.chmod(0o755)
    return {"PATH": str(kutu)}, iz


def test_j1_POZITIF_KONTROL_NISANCI_GERCEKTEN_OTER(tmp_path):
    """Nişancı ötmüyorsa j2 BOŞ bir çividir. Önce ötebildiğini göster."""
    ort, iz = _nisanci(tmp_path)
    r = _cli("durum", ort=ort)
    assert iz.exists(), (
        "nişancı ötmedi: `durum` ssh'ı hiç çalıştırmadı ya da PATH'ten çözmedi — "
        f"j2 çivisi ölçüm YAPAMAZ\nrc={r.returncode}\n{r.stdout}\n{r.stderr}")


@pytest.mark.parametrize("bayrak", [
    ("durum", "--komut-yaz"),
    ("journal", "bekci", "--komut-yaz"),
    ("oturumlar", "bekci", "--komut-yaz"),
    ("test-atesle", "bekci"),
    ("test-atesle", "bekci", "--kanit", "--komut-yaz"),
    ("profil-guncelle", "bekci"),
    # KRİTİK DAL (inceleme, düzeltme turu 1): `--uygula` GÜVENLİK BAYRAĞINI yok sayıyordu.
    ("profil-guncelle", "bekci", "--uygula", "--komut-yaz"),
])
def test_j2_TESTTE_SSH_HIC_CAGRILMAZ(tmp_path, bayrak):
    ort, iz = _nisanci(tmp_path)
    r = _cli(*bayrak, ort=ort)
    assert r.returncode == 0, f"{bayrak} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert not iz.exists(), (
        f"{bayrak} GERÇEKTEN ssh çalıştırdı: {iz.read_text(encoding='utf-8')!r}")

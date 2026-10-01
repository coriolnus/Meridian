"""test_dash_token_betigi_v559.py — TSK-064: `deploy/oracle-a1/dash_token_credential.sh` bir MEZAR TAŞIDIR
(Rol-1 kararı 2026-09-26): her çağrı — argümansız eski DURUM dahil, her bayrak — hiçbir şey okumadan ya da
yazmadan, hiçbir harici komut (sudo · systemctl · curl …) çağırmadan TEK bir açıklama basar ve ÇIKIŞ 2 ile döner.

NUMARA: v559 bu dosyanın kimliğidir (TSK-064 argv/basma dilimi, 46120fb4). Aynı betiğin emeklilik dilimi
aynı dosyayı UYARLAR — Rol-1 brief'i: yeni numara gerekmez.

NEDEN MEZAR TAŞI, NEDEN SİLİNMEDİ (karar Rol-1'in, gerekçesi betik başlığında — RUNBOOK'un kaynağı): geçiş
bitti (LoadCredential canlı, `.dash.env` 2026-09-14'te silindi, kaynak dosya Vault Agent render'ı); rotasyonun
yolu `sir_rotasyon.sh --dash --vault --uret`. Eski fazlar bugünkü düzende ölüydü (--faz1/--faz2) ya da
ZARARLIYDI (--geri-al tek kanalı kaldırıp pano jetonunu boşa düşürüyordu). Dosya yerinde kalır, çünkü tarihsel
belgeler ve RUNBOOK'a alıntılanan bir günlük yönergesi bu yolu gösteriyor: izleyen operatör "dosya yok" yerine
DOĞRU yolu bulur.

EMEKLİ EDİLEN ÇİVİLER (46120fb4..8ccbbb15 arası bu dosyada 46 çivi): A (başlık stdin'den · jeton değişkeni hiçbir
baskıya gitmez · kabuk sözcükleyicisi + 15 örnekli kontrolü · v556 sınıf taraması), B (ps: jeton hiçbir torunun
argv'sinde yok · çıktıda jeton yok · faz-1 yer beyanı), C (eski biçimle birebir davranış, 12 senaryo), D (bugünkü
dünya: faz1/faz2 ölü, --geri-al tek kanalı kaldırır — emeklilik KANITI), M (altı mutasyon). ÖLÇTÜKLERİ YÜZEY YOK
OLDU: betikte curl, jeton değişkeni, faz gövdesi kalmadı.
  · A/B'nin iddiası ("jeton argv'ye ve çıktıya girmez") burada GÜÇLENEREK yaşar: betik jeton TAŞIYAMAZ — gövde
    yalnız izinli bash yerleşikleridir (A1), komut ikamesi yoktur, dinamik koşumda tek bir harici komut bile
    çağrılmaz (B1). v556 sınıf taraması betikte SIFIR kimlik bayrağı görür (A3).
  · C'nin eşitlik iddiası BİLEREK bırakıldı: davranış değişti ve değişiklik kararın kendisidir.
  · D'nin kanıtı Rol-1 kararına girdi (brief 2026-09-26); D1'in çapraz kaynak denetimi burada mezar taşının
    GÖSTERDİĞİ YOLUN gerçek olduğunu ölçer (C bölümü).
  · Eski düzeneğin (şimler, systemctl modeli, sahte pano, sözcükleyici) yerini TEK bir kayıt düzeneği aldı.

BÖLÜMLER
  A  statik — gövde yalnız `set · printf · exit`; komut ikamesi yok; yönlendirme yalnız `>&2`; mesaj tanımı TEK;
     `set -euo pipefail` korunur · iskelet çıkarıcısının pozitif/negatif kontrolü (A2) · kimlik bayrağı yok (A3)
  B  dinamik — her mod: çıkış 2 · stdout BOŞ, stderr TEK satır = MESAJ · PATH YALNIZ kayıt şimleriyken çağrı
     kaydı BOŞ · hiçbir dosya yazılmadı (HOME · TMPDIR · cwd · betiğin kendi dizini) · düzeneğin pozitif kontrolü
  C  gösterilen yol GERÇEK — mesajdaki komut + bayraklar `sir_rotasyon.sh` ayrıştırıcısında, `--dash` kasa/üretim
     sınıfında; dosya Agent render hedefi + envanterde kasaya bağlı + LoadCredential kaynağı; başlık (RUNBOOK
     kaynağı) aynı yolu taşır (ayrışma çivisi)
  M  mutasyonlar — eski gövde bir modda geri gelir · çıkış 0 · yeni yol metni düşer · dosyaya yazım

SIR DEĞERİ YOK: betik değer taşımaz; bu dosyada da değer yoktur. Mutasyon fikstürü ESKİ gövdenin yan etkili iki
fonksiyonudur (8ccbbb15'ten birebir) ve yalnız KAYIT ŞİMLERİ altında koşar — hiçbir gerçek sudo/systemctl/curl
çağrılamaz (PATH yalnız şim dizini; şimsiz her harici komut 127 ile düşer, B0 bunu ölçer).
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import shutil
import stat
import subprocess

import pytest
import yaml

from tests.test_cp_rotasyon_v556 import _sinif_tara

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK_DEPO / "deploy" / "oracle-a1" / "dash_token_credential.sh"
DROPIN_50 = KOK_DEPO / "deploy" / "oracle-a1" / "meridian.service.d" / "50-dash-credential.conf"
ENVANTER = KOK_DEPO / "deploy" / "sir_envanteri.yaml"
AGENT_HCL = KOK_DEPO / "deploy" / "vault" / "agent.hcl"
SIR_ROTASYON = KOK_DEPO / "deploy" / "oracle-a1" / "sir_rotasyon.sh"
API_PY = KOK_DEPO / "meridian" / "api.py"
BASH = shutil.which("bash") or "/bin/bash"

#: Mezar taşının TEK açıklaması — Rol-1 brief'inin (2026-09-26) BİREBİR metni. Sözleşme pinidir: betikteki
#: tanım (A1) ve basılan satır (B1) buna eşit olmalı; metni değiştiren bu satırı da BİLEREK değiştirir.
MESAJ = ("EMEKLİ (2026-09-26, TSK-064): pano jetonu rotasyonu artık "
         "`sudo deploy/oracle-a1/sir_rotasyon.sh --dash --vault --uret` (önce `--kuru`); "
         "kanal Vault Agent render'ı → `/etc/meridian/dash_token` (LoadCredential)")
#: Betikteki tanım satırı: çift tırnak içinde backtick KAÇIŞLIDIR (kaçışsız backtick komut ikamesidir — A1 öter).
MESAJ_TANIMI = 'MESAJ="' + MESAJ.replace("`", "\\`") + '"\n'
YAZIM_SATIRI = "printf '%s\\n' \"$MESAJ\" >&2\n"

#: Eski çağrı biçimlerinin TAMAMI + iki çok-argümanlı birleşim. Hiçbiri özel değildir: mezar taşı argüman OKUMAZ.
MODLAR = [(), ("--faz1",), ("--faz2",), ("--geri-al",), ("--bilinmeyen",), ("--faz1", "--geri-al"),
          ("durum",)]
MOD_ADLARI = ["argumansiz", "faz1", "faz2", "geri-al", "bilinmeyen", "faz1+geri-al", "durum"]


# =================================================================================================
# A) STATİK — kod iskeleti: tam-satır ve satır-sonu yorumlar atılır, tırnak İÇERİKLERİ `Q`ya iner
# =================================================================================================
IZINLI_KOMUTLAR = frozenset({"set", "printf", "exit"})
_ANAHTAR = frozenset({"if", "then", "else", "elif", "fi", "do", "done", "case", "esac", "while", "until",
                      "for", "in", "!", "{", "}", "function", "select", "time"})
_ATAMA = re.compile(r"[A-Za-z_]\w*\+?=\S*")
_YONLENDIRME = re.compile(r"(?:\d+|&)?(?:>>|>&|<&|<<<|<<-?|>\||<>|>|<)[^\s;|()<>]*")


def _iskelet(metin: str) -> tuple[str, int]:
    """(iskelet, komut ikamesi sayısı). İkame: tırnak DIŞINDA ya da ÇİFT tırnak içinde `$(` veya kaçışsız
    backtick — tek tırnak içeriğini kabuk genişletmez, sayılmaz. Heredoc gövdesi bilinmez: `<<` zaten
    izinsiz yönlendirmedir (A1 öter). Backtick ÇİFT olarak açar-kapar: sayı kaçışsız backtick'lerin yarısıdır
    (yukarı yuvarlanır — kapanmamış tek backtick de bir ikame girişimidir)."""
    out: list[str] = []
    dolar, backtick, i, n = 0, 0, 0, len(metin)
    while i < n:
        c = metin[i]
        if c == "\\" and i + 1 < n:
            out.append(" " if metin[i + 1] == "\n" else "Q")
            i += 2
            continue
        if c == "'":
            j = metin.find("'", i + 1)
            out.append("Q")
            i = n if j < 0 else j + 1
            continue
        if c == '"':
            j = i + 1
            while j < n and metin[j] != '"':
                if metin[j] == "\\":
                    j += 2
                    continue
                backtick += metin[j] == "`"
                dolar += metin.startswith("$(", j)
                j += 1
            out.append("Q")
            i = j + 1
            continue
        backtick += c == "`"
        dolar += metin.startswith("$(", i)
        if c == "#" and (i == 0 or metin[i - 1] in " \t\n;"):
            j = metin.find("\n", i)
            i = n if j < 0 else j
            continue
        out.append(c)
        i += 1
    return "".join(out), dolar + (backtick + 1) // 2


def _yonlendirmeler(iskelet: str) -> list[str]:
    return _YONLENDIRME.findall(iskelet)


def _komutlar(iskelet: str) -> set[str]:
    """Her basit komutun KOMUT SÖZCÜĞÜ (baştaki atamalar ve anahtar sözcükler atlanır). Yönlendirmeler önce
    silinir: `>&2`deki `&` bir ayırıcı değildir."""
    out: set[str] = set()
    for parca in re.split(r"[\n;|&()]", _YONLENDIRME.sub(" ", iskelet)):
        sozcuk = parca.split()
        while sozcuk and (sozcuk[0] in _ANAHTAR or _ATAMA.fullmatch(sozcuk[0])):
            sozcuk.pop(0)
        if sozcuk:
            out.add(sozcuk[0])
    return out


def _statik_ihlaller(metin: str) -> list[str]:
    iskelet, ikame = _iskelet(metin)
    ihlal = [f"izinsiz komut: {k}" for k in _komutlar(iskelet) - IZINLI_KOMUTLAR]
    if ikame:
        ihlal.append(f"komut ikamesi: {ikame}")
    ihlal += [f"yönlendirme: {y}" for y in _yonlendirmeler(iskelet) if y != ">&2"]
    return sorted(ihlal)


def test_A0_BETIK_yerinde_CALISTIRILABILIR_sozdizimi_TEMIZ():
    """Dosya SİLİNMEDİ (Rol-1 kararı) ve `./dash_token_credential.sh` biçiminde çağrılabilir kalır — çalıştırma
    biti düşerse operatör mezar taşının açıklaması yerine "Permission denied" görür."""
    assert BETIK.is_file(), "mezar taşı yerinde değil"
    assert os.access(BETIK, os.X_OK), "çalıştırma biti yok"
    r = subprocess.run([BASH, "-n", str(BETIK)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr[-300:]


def test_A1_STATIK_govde_YALNIZ_set_printf_exit_ikame_YOK_yonlendirme_YALNIZ_stderr_mesaj_TEK_tanim():
    metin = BETIK.read_text(encoding="utf-8")
    ihlal = _statik_ihlaller(metin)
    assert ihlal == [], ihlal
    iskelet, _ = _iskelet(metin)
    komutlar = _komutlar(iskelet)
    # POZİTİF KONTROL: çıkarıcı gövdeyi GÖRÜYOR (boş küme de "izinsiz yok" derdi).
    assert komutlar == IZINLI_KOMUTLAR, sorted(komutlar)
    assert _yonlendirmeler(iskelet) == [">&2"]
    assert metin.count(MESAJ_TANIMI) == 1, "mesaj tanımı brief metnine birebir eşit değil ya da TEK değil"
    assert metin.count(YAZIM_SATIRI) == 1 and metin.count("\nexit 2\n") == 1
    assert re.search(r"(?m)^set -euo pipefail$", metin), "set -euo pipefail korunmadı"


ISKELET_ORNEKLERI = {
    "sudo rm -f /x\n": ["izinsiz komut: sudo"],
    "printf '%s' \"sudo curl systemctl\" >&2\n": [],
    'x="$(curl -s u)"\n': ["komut ikamesi: 1"],
    'x="a `id` b"\n': ["komut ikamesi: 1"],
    'x="a \\`id\\` b"\n': [],
    "x=$(id)\n": ["izinsiz komut: id", "komut ikamesi: 1"],
    "printf x > /tmp/f\n": ["yönlendirme: >"],
    "printf x 2>/dev/null\n": ["yönlendirme: 2>/dev/null"],
    "cat < /etc/passwd\n": ["izinsiz komut: cat", "yönlendirme: <"],
    "printf x | tee /tmp/f >/dev/null\n": ["izinsiz komut: tee", "yönlendirme: >/dev/null"],
    "exec 3>/tmp/f\n": ["izinsiz komut: exec", "yönlendirme: 3>/tmp/f"],
    "printf hi # sudo rm -rf /\n": [],
    "# sudo systemctl restart meridian\n": [],
    "A=1 systemctl restart x\n": ["izinsiz komut: systemctl"],
    "true && curl x || exit 2\n": ["izinsiz komut: curl", "izinsiz komut: true"],
    "/usr/bin/sudo ls\n": ["izinsiz komut: /usr/bin/sudo"],
    "eval 'sudo x'\n": ["izinsiz komut: eval"],
    "if [ -n x ]; then exit 2; fi\n": ["izinsiz komut: ["],
    "printf '%s\\n' \"$MESAJ\" >&2\nexit 2\n": [],
}


@pytest.mark.parametrize("ornek", list(ISKELET_ORNEKLERI))
def test_A2_ISKELET_CIKARICI_pozitif_ve_negatif_kontrol(ornek):
    assert _statik_ihlaller(ornek) == ISKELET_ORNEKLERI[ornek]


def test_A3_SINIF_TARAMASI_v556_betikte_SIFIR_kimlik_bayragi():
    """Eski A4'ün devamı: betik artık bir kimlik başlığı TAŞIYAMAZ — sayaç SIFIR (eskiden ≥1'di)."""
    ihlal, sayac = _sinif_tara([BETIK])
    assert ihlal == [] and sayac["arguman"] == 0, sayac


# =================================================================================================
# B) DİNAMİK — PATH YALNIZ kayıt şimleri; HOME · TMPDIR · cwd · betik dizini görüntülenir
# =================================================================================================
#: Eski gövdenin çağırdığı her harici komut + genel yazıcılar. Şim çağrıyı ADIYLA kaydeder ve HİÇBİR ŞEY
#: yapmaz (argümanlarını yürütmez). Listede olmayan her harici komut PATH'te YOKTUR → 127 (B0 ölçer).
KAYIT_SIMLERI = ("sudo", "systemctl", "curl", "install", "tee", "cp", "mv", "rm", "rmdir", "chmod", "chown",
                 "stat", "sed", "cat", "head", "tr", "awk", "seq", "sleep", "openssl", "grep", "date",
                 "dirname", "journalctl", "pgrep", "touch", "mkdir", "ln", "dd")
SIM = '#!/bin/sh\nprintf \'%s\\n\' "${0##*/} $*" >> "$SAHTE_KAYIT"\nexit 0\n'
GORUNTULENEN = ("ev", "gecici", "calisma", "betik")


def _goruntu(kok: pathlib.Path) -> dict[str, tuple]:
    out: dict[str, tuple] = {}
    for ad in GORUNTULENEN:
        for p in sorted((kok / ad).rglob("*")):
            st = p.lstat()
            ozet = hashlib.sha256(p.read_bytes()).hexdigest() if stat.S_ISREG(st.st_mode) else None
            out[p.relative_to(kok).as_posix()] = (stat.S_IFMT(st.st_mode), stat.S_IMODE(st.st_mode),
                                                   st.st_size, st.st_mtime_ns, ozet)
    return out


def _kos(kok: pathlib.Path, metin: str, *arg: str) -> dict:
    """Betik metnini `kok/betik/` altına koyar ve kayıt düzeneğinde koşar. Döner: çıkış kodu, iki akış, çağrı
    kaydı, DEĞİŞEN yollar (öncesi/sonrası görüntü farkı)."""
    for ad in ("bin", "kayit", *GORUNTULENEN):
        (kok / ad).mkdir(parents=True)
    for ad in KAYIT_SIMLERI:
        (kok / "bin" / ad).write_text(SIM, encoding="utf-8")
        (kok / "bin" / ad).chmod(0o755)
    for ad in GORUNTULENEN:
        (kok / ad / "kanarya").write_text("dokunulmaz\n", encoding="utf-8")
    betik = kok / "betik" / BETIK.name
    betik.write_text(metin, encoding="utf-8")
    betik.chmod(0o755)
    kayit = kok / "kayit" / "cagri.log"
    once = _goruntu(kok)
    ortam = {"PATH": str(kok / "bin"), "HOME": str(kok / "ev"), "TMPDIR": str(kok / "gecici"),
             "SAHTE_KAYIT": str(kayit)}
    r = subprocess.run([BASH, str(betik), *arg], cwd=kok / "calisma", env=ortam, capture_output=True,
                       text=True, encoding="utf-8", timeout=60)
    sonra = _goruntu(kok)
    return {"kod": r.returncode, "stdout": r.stdout, "stderr": r.stderr,
            "cagrilar": kayit.read_text(encoding="utf-8").splitlines() if kayit.exists() else [],
            "yazim": sorted(k for k in once.keys() | sonra.keys() if once.get(k) != sonra.get(k))}


def _ihlaller(s: dict) -> list[str]:
    """Mezar taşı sözleşmesinin DÜŞEN maddelerinin ADLARI (değer değil)."""
    ihlal = []
    if s["kod"] != 2:
        ihlal.append("çıkış kodu")
    if (s["stdout"], s["stderr"]) != ("", MESAJ + "\n"):
        ihlal.append("açıklama")
    if s["cagrilar"]:
        ihlal.append("çağrı")
    if s["yazim"]:
        ihlal.append("yazım")
    return ihlal


KONTROL = 'sudo true\nsystemctl --version\ncurl -s http://127.0.0.1:9/x\nprintf iz > "$HOME/iz"\nexit 2\n'


def test_B0_DUZENEK_pozitif_kontrol_simler_CAGRIYI_gorur_yazim_GORUNUR_simsiz_komut_DUSER(tmp_path):
    s = _kos(tmp_path / "k", KONTROL)
    assert [c.split()[0] for c in s["cagrilar"]] == ["sudo", "systemctl", "curl"], "şimler çağrıyı görmedi"
    assert "ev/iz" in s["yazim"], "görüntü yazımı görmedi"
    assert _ihlaller(s) == ["açıklama", "çağrı", "yazım"]
    s2 = _kos(tmp_path / "k2", "ls >/dev/null\n")
    assert s2["kod"] == 127, "şimsiz harici komut PATH'te bulundu — düzenek harici komutları süzmüyor"


@pytest.mark.parametrize("arg", MODLAR, ids=MOD_ADLARI)
def test_B1_HER_MOD_cikis_2_TEK_aciklama_HICBIR_cagri_HICBIR_yazim(tmp_path, arg):
    s = _kos(tmp_path, BETIK.read_text(encoding="utf-8"), *arg)
    ihlal = _ihlaller(s)
    assert ihlal == [], f"{ihlal} · kod={s['kod']} · çağrılar={s['cagrilar']} · yazım={s['yazim']}"


# =================================================================================================
# C) GÖSTERİLEN YOL GERÇEK — mezar taşı operatörü var olmayan bir komuta ya da bayrağa gönderemez
# =================================================================================================
def _mesaj_parcalari() -> tuple[str, str, str]:
    komut, kuru, dosya = re.findall(r"`([^`]+)`", MESAJ)
    return komut, kuru, dosya


def _ayristirici_bayraklari(metin: str) -> set[str]:
    # 2026-10-01 (G3b Task 3): ayrıştırıcı `while`/`shift` döngüsüne döndü (`--kapi-bot <ad>` iki jetondur); gövde aynı `case`.
    dongu = re.search(r'(?ms)^(?:for _a in "\$@"; do|while \[ "\$#" -gt 0 \]; do\n  _a="\$1"; shift)\n'
                      r'  case "\$_a" in\n(.*?)^  esac\ndone', metin)
    assert dongu, "sir_rotasyon.sh ana ayrıştırıcısı bulunamadı (ölçüm kör)"
    return {b for d in re.findall(r"(?m)^\s*([-\w|]+)\)", dongu.group(1)) for b in d.split("|")}


def test_C1_KOMUT_VAR_bayraklari_sir_rotasyonun_AYRISTIRICISINDA_dash_URETIM_sinifinda():
    komut, kuru, _ = _mesaj_parcalari()
    sozcuk = komut.split()
    assert sozcuk[0] == "sudo" and (KOK_DEPO / sozcuk[1]).resolve() == SIR_ROTASYON.resolve()
    assert os.access(SIR_ROTASYON, os.X_OK), "gösterilen betik çalıştırılabilir değil"
    rot = SIR_ROTASYON.read_text(encoding="utf-8")
    taninan = _ayristirici_bayraklari(rot)
    assert {"--kuru", "--envanter"} <= taninan, "ayrıştırıcı bilinen bayrakları görmüyor (ölçüm kör)"
    eksik = [b for b in [*sozcuk[2:], kuru] if b not in taninan]
    assert eksik == [], f"sir_rotasyon.sh tanımıyor: {eksik}"
    assert re.search(r"(?m)^dash\(\) \{", rot), "--dash alt komutu yok"
    assert re.search(r"(?m)^\s*kapi\|dash\|apisix-admin\) echo b64 ;;", rot), "--dash --uret üretim sınıfı yok"


def test_C2_DOSYA_Agent_RENDER_HEDEFI_kasaya_BAGLI_LoadCredential_KAYNAGI():
    _, _, dosya = _mesaj_parcalari()
    assert f'destination = "{dosya}"' in AGENT_HCL.read_text(encoding="utf-8"), "Agent render hedefi değil"
    girdi = [g for g in yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"] if g.get("hedef") == dosya]
    assert len(girdi) == 1 and girdi[0].get("rotasyon_siri") == "MERIDIAN_DASH_TOKEN", "kasaya bağlı değil"
    rot = SIR_ROTASYON.read_text(encoding="utf-8")
    assert f"dash MERIDIAN_DASH_TOKEN dosya {dosya} " in rot, "rotasyon tablosu bu dosyayı yazmıyor"
    lc = re.findall(r"(?m)^LoadCredential=(\w+):(\S+)$", DROPIN_50.read_text(encoding="utf-8"))
    ad = re.findall(r'(?m)^CRED_DOSYA_ADI = "(\w+)"', API_PY.read_text(encoding="utf-8"))
    assert lc == [(ad[0], dosya)] and len(ad) == 1, "LoadCredential kaynağı/adı uygulamanın okuduğu değil"


def test_C3_BASLIK_RUNBOOK_kaynagi_AYNI_yolu_tasir_ve_EMEKLI_der():
    """Başlık ile mesaj aynı gerçeğin iki kopyasıdır (başlık RUNBOOK'a gider, mesaj terminale) — ayrışma çivisi."""
    satirlar = BETIK.read_text(encoding="utf-8").splitlines()
    baslik = []
    for s in satirlar[1:]:
        if not s.startswith("#"):
            break
        baslik.append(s[1:])
    metin = " ".join(" ".join(baslik).split())
    eksik = [p for p in (*_mesaj_parcalari(), "EMEKLİ (2026-09-26, TSK-064)") if p not in metin]
    assert eksik == [], f"başlıkta yok: {eksik}"


# =================================================================================================
# M) MUTASYONLAR — mutant tmp'de koşar, özgün betik değişmez
# =================================================================================================
#: ESKİ GÖVDENİN yan etkili iki modu — 8ccbbb15'teki `deploy/oracle-a1/dash_token_credential.sh`ten BİREBİR
#: (sabitler + yardımcılar + `durum` + `geri_al`). Yalnız kayıt şimleri altında koşar.
ESKI_GOVDE = r'''BIRIM=/etc/systemd/system/meridian.service.d
KRED=/etc/meridian/dash_token
ENVF=/opt/meridian/.dash.env
API=http://127.0.0.1:8080

die() { echo "!! $*" >&2; exit 1; }
oldu() { echo "  ✓ $*"; }

_servis_ayakta() {
  systemctl is-active --quiet meridian || return 1
  for _ in $(seq 1 30); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)" = "200" ] && return 0
    sleep 1
  done
  return 1
}

durum() {
  echo "=== DURUM ==="
  echo "  systemd sürümü: $(systemctl --version | head -1)"
  echo "  credential kaynağı ($KRED): $(sudo test -s "$KRED" && sudo stat -c '%a %U:%G' "$KRED" || echo YOK)"
  echo "  ortam dosyası ($ENVF): $(sudo test -s "$ENVF" && sudo stat -c '%a %U:%G' "$ENVF" || echo YOK)"
  for f in 50-dash-credential.conf 51-dash-env-kaldir.conf; do
    echo "  drop-in $f: $([ -f "$BIRIM/$f" ] && echo KURULU || echo yok)"
  done
  echo "  LoadCredential (yürürlükte): $(systemctl show meridian -p LoadCredential --value || true)"
  echo "  servis: $(systemctl is-active meridian) · healthz: $(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)"
}

geri_al() {
  echo "=== GERİ ALMA: ortam kanalına dön ==="
  sudo rm -f "$BIRIM/51-dash-env-kaldir.conf" "$BIRIM/50-dash-credential.conf"
  sudo rmdir "$BIRIM" 2>/dev/null || true
  sudo systemctl daemon-reload; sudo systemctl restart meridian
  _servis_ayakta && oldu "drop-in'ler kaldırıldı, servis ayakta ($ENVF yürürlükte)" \
                 || die "servis açılmadı — journalctl -u meridian -n 50"
  echo "  · $KRED SİLİNMEDİ (bilinçli: geri almanın kendisi geri alınabilir kalsın)."
}
'''


def _degistir(metin: str, eski: str, yeni: str) -> str:
    adet = metin.count(eski)
    assert adet == 1, f"çapa sayısı {adet} ≠ 1: {eski[:60]!r}"
    return metin.replace(eski, yeni)


@pytest.mark.parametrize("arg,fonksiyon", [(("--geri-al",), "geri_al"), ((), "durum")],
                         ids=["geri-al", "argumansiz"])
def test_M1_MUT_ESKI_GOVDE_bir_modda_GERI_GELIRSE_B1_ve_A1_KIRMIZI(tmp_path, arg, fonksiyon):
    kosul = f'"{arg[0]}"' if arg else '""'
    mutant = _degistir(BETIK.read_text(encoding="utf-8"), YAZIM_SATIRI,
                       ESKI_GOVDE + f'case "${{1:-}}" in {kosul}) {fonksiyon} ;; esac\n' + YAZIM_SATIRI)
    s = _kos(tmp_path, mutant, *arg)
    ihlal = _ihlaller(s)
    assert {"açıklama", "çağrı"} <= set(ihlal), f"B1 kör: {ihlal}"
    adlar = {c.split()[0] for c in s["cagrilar"]}
    assert {"sudo", "systemctl"} <= adlar, f"eski gövdenin çağrıları kayda düşmedi: {sorted(adlar)}"
    statik = _statik_ihlaller(mutant)
    assert "izinsiz komut: echo" in statik and any(i.startswith("komut ikamesi") for i in statik), statik


def test_M2_MUT_cikis_0_OLURSA_B1_KIRMIZI(tmp_path):
    mutant = _degistir(BETIK.read_text(encoding="utf-8"), "\nexit 2\n", "\nexit 0\n")
    assert _ihlaller(_kos(tmp_path, mutant)) == ["çıkış kodu"]


def test_M3_MUT_yeni_YOL_metni_DUSERSE_B1_ve_A1_KIRMIZI(tmp_path):
    komut, _, _ = _mesaj_parcalari()
    mutant = _degistir(BETIK.read_text(encoding="utf-8"), "\\`" + komut + "\\` ", "")
    assert _ihlaller(_kos(tmp_path, mutant, "--faz1")) == ["açıklama"]
    assert mutant.count(MESAJ_TANIMI) == 0, "A1'in mesaj tanımı pini kör"


def test_M4_MUT_dosyaya_YAZARSA_B1_ve_A1_KIRMIZI(tmp_path):
    mutant = _degistir(BETIK.read_text(encoding="utf-8"), YAZIM_SATIRI,
                       YAZIM_SATIRI + 'printf \'%s\\n\' "$MESAJ" > "$HOME/mezar_izi"\n')
    assert _ihlaller(_kos(tmp_path, mutant, "--geri-al")) == ["yazım"]
    assert _statik_ihlaller(mutant) == ["yönlendirme: >"]

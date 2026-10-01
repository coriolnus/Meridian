"""test_sir_yazim_yolu_v609.py — TSK-260: sır rotasyon aracının KENDİ yazım yolunda sembolik bağ / yol tabanlı chown sınıfı.

NUMARA: `ls tests | grep v609` boş — bu worktree, ana checkout ve bütün `.claude/worktrees/*/tests` (ölçüldü 2026-10-01; en
yüksek v608).

SINIF (CWE-59). G3b tohumlama yolu (`tohumla-env`) 87d194b3'te kapandı; AYNI sınıf rotasyonun yazım yolunda açıktı:
`_atomik_yaz` (`yaz-env` · `yaz-dosya` · `yaz-url` · `bosalt` · çalışma dizini çıktıları) `mkstemp(dir=…)` + YOL tabanlı
`os.chmod`/`os.chown` + `os.replace(yol)` kullanıyordu. Üç delik: (1) ubuntu kimliği geçici adı chown'dan ÖNCE bir bağa
çevirirse root bağın HEDEFİNİN sahibini/modunu değiştirir; (2) hedef dizinin (ya da zincirdeki bir bileşenin) bağ olması yazımı
ağacın DIŞINA götürür; (3) hedef `.env`in kendisi bağsa root içeriği bağın hedefinden okur, `koru` izni oradan alır ve bağı
düz dosyayla ezer. Ubuntu sahipli dizinler: hermes profilleri (`~/.hermes/…`), bot ağ geçidi (`~/.hermes-botlar/…`),
`/opt/hindsight` (755 ubuntu — A1 ölçümü 2026-09-15, `deploy/vault/vault-agent.service` başlığı).

YENİ SÖZLEŞME — yardımcının TEK yazım gövdesi (`_atomik_yaz` → `_hedef_ac` · `_gecici_yaz` · `_yazim_kusurlari`; zincir
denetimi tohumlamanın `_dizin_ac`ıdır, kopya DEĞİL):
  · zincir GÜVEN ÇAPASINDAN aşağı bileşen bileşen `O_NOFOLLOW|O_DIRECTORY` (openat) ile açılır, her bileşen tanıtıcıdan
    ölçülür: bağ değil · dizin · grup/diğer YAZAMAZ · sahibi root ya da HEDEFİN sahibi (root iken — OpenSSH `safe_path`
    kuralı: "dizin, hedefin yazılacağı kullanıcı dışında kimse tarafından yazılamaz"; Debian yamasıyla grup-yazma YALNIZ grup
    sahibine özelse ve root iken zararsız — Ubuntu kullanıcı oturumunun umask 002'si, B3);
  · hedef VARSA `lstat`: bağ ya da normal dosya değilse RED, yazım YOK; `koru` mod/sahibi bu `lstat`tan;
  · oku-değiştir-yaz (`yaz-env`/`yaz-url`) eski içeriği AYNI dizin tanıtıcısından `O_NOFOLLOW` ile okur;
  · geçici dosya dizin tanıtıcısına göre `O_EXCL|O_NOFOLLOW`, sahip/mod DOSYA TANITICISINA (`fchown` → `fchmod`);
  · yerine koymadan ÖNCE geçici ad yeniden ölçülür (yarışta değiştiyse yerine KONMAZ), `os.replace(dir_fd)`;
  · yazım SONRASI `lstat`: aynı inode · normal dosya · beklenen mod · beklenen sahip (root iken).
  Ön-denetim (`_hedef_on_denetim` → `py hedef-denetle`) aynı `_hedef_ac`ı `env` hedeflerinde HİÇBİR yazımdan ÖNCE koşar —
  bağlı/gevşek bir hedef rotasyonu YARIDA bırakmaz, hiç başlatmaz.

ÇAPA. Üretimde kök `/` (betiğin `KOK`u boş); çivide `SIR_ROT_KOK` (kabuktaki TEST KANCASIYLA AYNI değişken). İkinci çapa
yardımcının KENDİ dizinidir (betiğin 0700 çalışma dizini, `_islik_kur`): o dizine güvenmeyen bir denetim koştuğu kodun
kendisine güvenmektedir — çapa yeni bir güven varsayımı EKLEMEZ. Bu dosya yardımcıyı ayrı bir 0700 `islik/` dizinine keser
(üretimin modeli): tmp_path'in kendisi çapa OLMAZ, "çapa dışı" ölçümü anlamlı kalır.

ROOT MODELİ. Çivi makinesinde root değiliz: sahip kuralı (yalnız root iken ölçülür) `os.geteuid` 0'a ve `pwd`/`grp` adları
seçilen uid/gid'e çözülerek sınanır (v604 D10b emsali). Dizinler test kullanıcısınındır; `root` adı test kullanıcısına
çözüldüğünde "root dizininde root hedefi" modellenir, `ubuntu` başka bir uid'e çözüldüğünde "dizin hedefin sahibine ait değil".

ÇIKTI DİSİPLİNİ: iddialar bool'a indirgenir (`_iddia`); değerler SAHTEdir ve hiçbir çıktıda görünmemelidir.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from tests.test_sir_rotasyon_v447 import BETIK, _kos, _sahte_ortam, _yardimci

ALAN = "OPENROUTER_API_KEY"
YENI = "SAHTE-V609-YENI-0001"
ESKI_ENV = "SAHTE-V609-ESKI-ENV-0002"
ESKI_DOSYA = "SAHTE-V609-ESKI-DOSYA-0003"
KURBAN = "SAHTE-V609-KURBAN-0004"
DISARI_DEGER = "SAHTE-V609-DISARI-0005"
_DEGERLER = (YENI, ESKI_ENV, ESKI_DOSYA, KURBAN, DISARI_DEGER)


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _iddia(kosul: bool, mesaj: str) -> None:
    """Bool iddia — pytest içgözlemi işlenenleri (değer taşıyabilir) basmaz."""
    if not kosul:
        pytest.fail(mesaj, pytrace=False)


def _maskeli(metin: str) -> str:
    for d in _DEGERLER:
        metin = metin.replace(d, "<SAHTE-DEGER>")
    return metin


def _ozet(r: subprocess.CompletedProcess) -> str:
    return f"çıkış {r.returncode}\n--- stdout ---\n{_maskeli(r.stdout)[-2500:]}\n--- stderr ---\n{_maskeli(r.stderr)[-2500:]}"


def _sizinti_yok(r: subprocess.CompletedProcess) -> None:
    _iddia(not any(d in r.stdout + r.stderr for d in _DEGERLER), "bir SAHTE değer çıktıya düştü")


def _imza(p: pathlib.Path) -> tuple:
    """Bayt + mod + inode + sahip — bağ İZLENİR (bağın hedefinin imzası)."""
    st = p.stat()
    return hashlib.sha256(p.read_bytes()).hexdigest(), st.st_mode & 0o7777, st.st_ino, st.st_uid, st.st_gid


def _agac_imzasi(kok: pathlib.Path) -> dict[str, tuple]:
    """Bir ağacın bütün girdileri (bağ İZLENMEDEN): ad → (tür, bayt sha256 | bağ hedefi, mod)."""
    sonuc = {}
    for p in sorted(kok.rglob("*")):
        st = p.lstat()
        if p.is_symlink():
            sonuc[str(p.relative_to(kok))] = ("bag", os.readlink(p), 0)
        elif p.is_file():
            sonuc[str(p.relative_to(kok))] = ("dosya", hashlib.sha256(p.read_bytes()).hexdigest(), st.st_mode & 0o7777)
        else:
            sonuc[str(p.relative_to(kok))] = ("dizin", "", st.st_mode & 0o7777)
    return sonuc


def _kalinti(*dizinler: pathlib.Path) -> list[str]:
    return [str(q) for d in dizinler if d.is_dir() for q in d.rglob(".sir-rot-*")]


def _yk(yardimci: pathlib.Path, op: str, *args, kok: pathlib.Path, on: str = "") -> subprocess.CompletedProcess:
    """Gömülü yardımcıyı DOĞRUDAN koşar. `kok` = `SIR_ROT_KOK` (betiğin test kancası — yardımcı aynı değişkenden okur);
    `on` yardımcıdan ÖNCE çalışan yama kodudur (yarış / root modeli)."""
    kod = (on + "import runpy, sys\n"
           f"sys.argv = {[str(yardimci), op, *map(str, args)]!r}\n"
           f"runpy.run_path({str(yardimci)!r}, run_name='__main__')\n")
    ortam = {k: v for k, v in os.environ.items() if k != "SIR_ROT_KOK"}
    ortam["SIR_ROT_KOK"] = str(kok)
    return subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, env=ortam)


def _root_modeli(adlar: dict[str, tuple[int, int]]) -> str:
    """`os.geteuid` 0 ve verilen ADLAR verilen (uid, gid)'e çözülür (yardımcı `pwd`/`grp`ı içeride ithal eder)."""
    return ("import os, pwd, grp\nos.geteuid = lambda: 0\n"
            f"_ADLAR = {adlar!r}\n"
            "class _K:\n    def __init__(s, u):\n        s.pw_uid = u\n"
            "class _G:\n    def __init__(s, g):\n        s.gr_gid = g\n"
            "_p, _g = pwd.getpwnam, grp.getgrnam\n"
            "pwd.getpwnam = lambda a: _K(_ADLAR[a][0]) if a in _ADLAR else _p(a)\n"
            "grp.getgrnam = lambda a: _G(_ADLAR[a][1]) if a in _ADLAR else _g(a)\n")


class _Sahne:
    """Yardımcı katmanının sahnesi: sahte kök (A1 yolları), çapa dışı `disari/`, 0700 `islik/` (yardımcı + değer dosyası)."""

    def __init__(self, tmp_path: pathlib.Path) -> None:
        self.tmp = tmp_path
        self.islik = tmp_path / "islik"
        self.islik.mkdir(mode=0o700)
        self.islik.chmod(0o700)
        self.yardimci = _yardimci(self.islik)
        self.kok = tmp_path / "kok"
        self.profil = self.kok / "home/ubuntu/.hermes/profiles/sef"
        self.profil.mkdir(parents=True)
        (self.kok / "etc/meridian").mkdir(parents=True)
        (self.kok / "etc/hindsight/creds").mkdir(parents=True)
        self.disari = tmp_path / "disari"
        self.disari.mkdir()
        # umask'tan bağımsız: zincirin her dizini 0755 (A1'in ölçülen hâli — /etc/meridian 0755 root, 2026-09-07).
        for d in [self.kok, *self.kok.rglob("*"), self.disari]:
            if d.is_dir():
                d.chmod(0o755)
        self.env = self.profil / ".env"
        self.env.write_text(f"HERMES_HOME=/home/ubuntu/.hermes/profiles/sef\n{ALAN}={ESKI_ENV}\n", encoding="utf-8")
        self.env.chmod(0o640)
        self.dosya = self.kok / "etc/meridian/kapi_apikey"
        self.dosya.write_text(ESKI_DOSYA + "\n", encoding="utf-8")
        self.dosya.chmod(0o400)
        self.url = self.kok / "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL"
        self.url.write_text("postgresql://hindsight:eski-parola@127.0.0.1:5432/hindsight\n", encoding="utf-8")
        self.url.chmod(0o400)
        self.bos = self.kok / "etc/meridian/nous_api_key"
        self.bos.write_text(ESKI_DOSYA + "\n", encoding="utf-8")
        self.bos.chmod(0o400)
        self.dgr = self.islik / "yeni"
        self.dgr.write_text(YENI + "\n", encoding="utf-8")
        self.dgr.chmod(0o600)

    def argv(self, op: str) -> tuple[pathlib.Path, tuple, str, str]:
        """op → (hedef, argümanlar, mod, sahip) — tablodaki biçimlerle (env/url `koru koru`; dosya `0400 root:root`)."""
        if op == "yaz-env":
            return self.env, (self.env, ALAN, self.dgr, "koru", "koru", "-"), "koru", "koru"
        if op == "yaz-dosya":
            return self.dosya, (self.dosya, self.dgr, "0400", "root:root", "-"), "0400", "root:root"
        if op == "yaz-url":
            return self.url, (self.url, self.dgr, "koru", "koru"), "koru", "koru"
        return self.bos, (self.bos, "0400", "root:root"), "0400", "root:root"

    def kos(self, op: str, *args, on: str = "", kok: pathlib.Path | None = None) -> subprocess.CompletedProcess:
        return _yk(self.yardimci, op, *args, kok=self.kok if kok is None else kok, on=on)


YAZIM_OPLARI = ("yaz-env", "yaz-dosya", "yaz-url", "bosalt")


# =================================================================================================
# (a) HEDEFİN KENDİSİ SEMBOLİK BAĞ → YAZIM YOK, bağın hedefi BAYT-EŞİT
# =================================================================================================

@pytest.mark.parametrize("op", YAZIM_OPLARI)
def test_A_HEDEF_sembolik_bag_ise_YAZIM_YOK_bagin_hedefi_BAYT_ESIT(tmp_path, op):
    """Hedef bir dosyaya bağ (ubuntu kendi dizininde `.env`i `/etc/…`ye bağlayabilir). ESKİ yol: `_oku` bağı izleyip içeriği
    hedeften okur, `koru` izni `os.stat` ile bağın hedefinden alır ve `os.replace` bağı DÜZ DOSYAYLA ezer — çıkış 0. YENİ yol:
    RED (`hedef SEMBOLİK BAĞ`), bağ yerinde, bağın hedefi bayt/mod/inode/sahip olarak aynı, geçici dosya kalmaz. Ön-denetim
    işlemi (`hedef-denetle`) AYNI hükmü basar (tek gövde: `_hedef_ac`)."""
    s = _Sahne(tmp_path)
    hedef, args, mod, sahip = s.argv(op)
    kurban = s.disari / "kurban"
    if op == "yaz-env":
        kurban.write_text(f"{ALAN}={KURBAN}\nBASKA=kalir\n", encoding="utf-8")
    elif op == "yaz-url":
        kurban.write_text(f"postgresql://hindsight:{KURBAN}@127.0.0.1:5432/hindsight\n", encoding="utf-8")
    else:
        kurban.write_text(KURBAN + "\n", encoding="utf-8")
    kurban.chmod(0o644)
    hedef.unlink()
    hedef.symlink_to(kurban)
    once = _imza(kurban)
    r = s.kos(op, *args)
    _iddia(hedef.is_symlink() and os.readlink(hedef) == str(kurban), "hedef bağ DÜZ DOSYAYLA ezildi")
    _iddia(_imza(kurban) == once, "bağın HEDEFİ değişti (bayt/mod/inode/sahip)")
    _iddia(r.returncode != 0 and "SEMBOLİK BAĞ" in r.stderr and "yazım YAPILMADI" in r.stderr, _ozet(r))
    _iddia(not _kalinti(hedef.parent, s.disari), f"geçici dosya kaldı: {_kalinti(hedef.parent, s.disari)}")
    _sizinti_yok(r)
    rd = s.kos("hedef-denetle", hedef, mod, sahip)
    _iddia(rd.returncode == 0 and rd.stdout.startswith("RED:") and "SEMBOLİK BAĞ" in rd.stdout, _ozet(rd))


# =================================================================================================
# (b) DİZİN ZİNCİRİNDE BAĞ ya da GEVŞEK İZİN → YAZIM YOK
# =================================================================================================

@pytest.mark.parametrize("hal", ["ebeveyn_bag", "ara_bag", "kok_bag", "grup_yazar", "diger_yazar"])
def test_B_DIZIN_zincirinde_bag_ya_da_gevsek_izin_YAZIM_YOK(tmp_path, hal):
    """`yaz-env` (`koru koru`, hermes profili). (ebeveyn_bag) `profiles/sef` başka bir dizine bağ; (ara_bag) `.hermes`
    bağ; (kok_bag) güven çapasının KENDİSİ bağ; (grup_yazar) `profiles/` 0775; (diger_yazar) `.hermes` 0757. ESKİ yol bağı
    izleyip ağacın DIŞINDAKİ `.env`i yazıyor ya da gevşek dizine yazıyordu (çıkış 0). YENİ: RED + sebep, bağın hedefindeki
    `.env` BAYT-EŞİT, geçici dosya kalmaz."""
    s = _Sahne(tmp_path)
    kok, hedef = s.kok, s.env
    if hal == "ebeveyn_bag":
        gercek = s.disari / "sef_gercek"
        s.profil.rename(gercek)
        s.profil.symlink_to(gercek, target_is_directory=True)
        izlenen, neden = gercek / ".env", "SEMBOLİK BAĞ"
    elif hal == "ara_bag":
        hermes = s.kok / "home/ubuntu/.hermes"
        gercek = s.disari / "hermes_gercek"
        hermes.rename(gercek)
        hermes.symlink_to(gercek, target_is_directory=True)
        izlenen, neden = gercek / "profiles/sef/.env", "SEMBOLİK BAĞ"
    elif hal == "kok_bag":
        kok = tmp_path / "kok_bag"
        kok.symlink_to(s.kok, target_is_directory=True)
        hedef = kok / "home/ubuntu/.hermes/profiles/sef/.env"
        izlenen, neden = s.env, "SEMBOLİK BAĞ"
    elif hal == "grup_yazar":
        (s.kok / "home/ubuntu/.hermes/profiles").chmod(0o775)
        izlenen, neden = s.env, "YAZABİLİR"
    else:
        (s.kok / "home/ubuntu/.hermes").chmod(0o757)
        izlenen, neden = s.env, "YAZABİLİR"
    once = _imza(izlenen)
    r = s.kos("yaz-env", hedef, ALAN, s.dgr, "koru", "koru", "-", kok=kok)
    _iddia(_imza(izlenen) == once, f"{hal}: .env YAZILDI (bağ izlendi ya da gevşek dizine yazıldı)")
    _iddia(r.returncode != 0 and neden in r.stderr and "yazım YAPILMADI" in r.stderr, _ozet(r))
    _iddia(not _kalinti(s.kok, s.disari), f"geçici dosya kaldı: {_kalinti(s.kok, s.disari)}")
    _sizinti_yok(r)


def _ozel_grup_modeli(gid: int, uid: int, birincil: list[str], ek: list[str], root: bool = True) -> str:
    """(Root modeli +) grup üyeliği modeli: `gid` grubunun birincil üyeleri `birincil` (pwd taraması), ek üyeleri `ek` (gr_mem);
    `uid` (dizin sahibi) `sahip-model` adına çözülür. `root=False`: yalnız üyelik modeli (kimlik root DEĞİL)."""
    return ((_root_modeli({}) if root else "import os, pwd, grp\n") +
            "class _GG:\n    def __init__(s, m):\n        s.gr_mem = m\n"
            "class _PW:\n    def __init__(s, n, u, g):\n        s.pw_name, s.pw_uid, s.pw_gid = n, u, g\n"
            f"_GID, _UID, _BIR, _EK = {gid!r}, {uid!r}, {birincil!r}, {ek!r}\n"
            "_ggid, _guid = grp.getgrgid, pwd.getpwuid\n"
            "grp.getgrgid = lambda g: _GG(list(_EK)) if g == _GID else _ggid(g)\n"
            "pwd.getpwuid = lambda u: _PW('sahip-model', _UID, _GID) if u == _UID else _guid(u)\n"
            "pwd.getpwall = lambda: [_PW(n, 90000 + i, _GID) for i, n in enumerate(_BIR)]\n")


@pytest.mark.parametrize("hal", ["ozel_grup", "baska_birincil_uye", "ek_uye", "uyesiz_grup", "root_degil_kati"])
def test_B3_GRUP_YAZMA_yalniz_SAHIBE_OZEL_grupta_ve_root_iken_ZARARSIZ(tmp_path, hal):
    """Ubuntu kullanıcı oturumunda umask 002'dir (`USERGROUPS_ENAB` + pam_umask): ubuntu'nun elle açtığı hermes dizini 0775
    ubuntu:ubuntu doğar ve grubun TEK üyesi ubuntu'dur — "hedefin sahibi dışında kimse yazamaz" kuralını BOZMAZ (Debian OpenSSH
    `secure_permissions` emsali). Root modeliyle `profiles/` 0775: (ozel_grup) grubun tek üyesi dizin sahibi → yazılır;
    (baska_birincil_uye / ek_uye) grupta başka bir hesap → RED "özel DEĞİL"; (uyesiz_grup) üye yok → RED (zararsızlık
    gösterilemedi); (root_degil_kati) root değilken üyelik ölçülmez → KATI ret. Diğer-yazma her kimlikte ret (B · F)."""
    s = _Sahne(tmp_path)
    profiles = s.kok / "home/ubuntu/.hermes/profiles"
    profiles.chmod(0o775)
    st = profiles.stat()
    birincil, ek = {"ozel_grup": (["sahip-model"], []), "baska_birincil_uye": (["sahip-model", "baska"], []),
                    "ek_uye": (["sahip-model"], ["baska"]), "uyesiz_grup": ([], []),
                    "root_degil_kati": (["sahip-model"], [])}[hal]
    # `root_degil_kati`: grup üyeliği ÖZEL modellenir ama kimlik root DEĞİL — istisna yalnız root iken sorulmalı (ortamdan
    # bağımsız ölçüm: gerçek grup verisine dayansaydı Linux'un kullanıcıya özel grubu ile macOS'un `staff`ı ayrı hüküm verirdi).
    on = _ozel_grup_modeli(st.st_gid, st.st_uid, birincil, ek, root=hal != "root_degil_kati")
    once = _imza(s.env)
    r = s.kos("yaz-env", s.env, ALAN, s.dgr, "koru", "koru", "-", on=on)
    if hal == "ozel_grup":
        _iddia(r.returncode == 0 and r.stdout == "" and f"{ALAN}={YENI}\n" in s.env.read_text(encoding="utf-8"), _ozet(r))
    else:
        _iddia(_imza(s.env) == once, f"{hal}: .env YAZILDI")
        beklenen = "YAZABİLİR" if hal == "root_degil_kati" else "özel DEĞİL"
        _iddia(r.returncode != 0 and beklenen in r.stderr and "yazım YAPILMADI" in r.stderr, _ozet(r))
    _iddia(not _kalinti(s.kok), f"geçici dosya kaldı: {_kalinti(s.kok)}")
    _sizinti_yok(r)


#: YARIŞ MODELİ — bileşen, zincir denetimi (`lstat`) GEÇTİKTEN SONRA ve açılış ANINDA bağa çevrilir, açılıştan hemen sonra
#: GERİ çevrilir (çift yarış: sonradan koşan `realpath` katmanı gerçeği görür). Böylece `O_NOFOLLOW` TEK BAŞINA ölçülür.
_ACILIS_YARISI = '''import os
_o = os.open
_ATES = []
def _open(p, flags, mode=0o777, *, dir_fd=None):
    if dir_fd is not None and p == __BILESEN__ and flags & os.O_DIRECTORY and not _ATES:
        _ATES.append(1)
        open(__ISARET__, "w").close()
        os.rename(p, p + "_gercek", src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
        os.symlink(__DISARI__, p, dir_fd=dir_fd)
        try:
            return _o(p, flags, mode, dir_fd=dir_fd)
        finally:
            os.unlink(p, dir_fd=dir_fd)
            os.rename(p + "_gercek", p, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    return _o(p, flags, mode, dir_fd=dir_fd)
os.open = _open
'''


@pytest.mark.parametrize("op", ["yaz-dosya", "yaz-env"])
def test_B2_YARIS_bilesen_ACILIS_aninda_baga_cevrilir_O_NOFOLLOW_izlemez(tmp_path, op):
    """Zincir bileşeni (`meridian` / `sef`) denetimden SONRA, açılış ANINDA çapa dışındaki bir dizine bağ olur ve açılıştan
    hemen sonra geri döner. `O_NOFOLLOW|O_DIRECTORY` açılışı reddeder → RED, dışarıdaki dizin BAYT-EŞİT. `yaz-dosya` (açık
    mod/sahip) bu yarışın TEK savunmasıdır: `O_NOFOLLOW` kalkarsa yazım dışarıya gider. `yaz-env` (`koru`) ikinci katman da
    taşır (`lstat` öncesi/sonrası inode eşitliği) — mutasyonda yeşil kalması beklenir ve beyanlıdır. Kanca ATEŞLENDİ mi ayrıca
    ölçülür (pozitif kontrol)."""
    s = _Sahne(tmp_path)
    hedef, args, _, _ = s.argv(op)
    bilesen = hedef.parent.name
    disari = s.disari / f"{bilesen}_sahte"
    disari.mkdir(mode=0o755)
    (disari / hedef.name).write_text(f"{ALAN}={DISARI_DEGER}\n" if op == "yaz-env" else DISARI_DEGER + "\n",
                                     encoding="utf-8")
    isaret = tmp_path / "kanca_atesledi"
    on = (_ACILIS_YARISI.replace("__BILESEN__", repr(bilesen)).replace("__ISARET__", repr(str(isaret)))
          .replace("__DISARI__", repr(str(disari))))
    once_d, once_h = _agac_imzasi(disari), _imza(hedef)
    r = s.kos(op, *args, on=on)
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    _iddia(_agac_imzasi(disari) == once_d, "yazım bağı İZLEDİ — çapa dışındaki dizin değişti")
    _iddia(_imza(hedef) == once_h, "gerçek hedef değişti")
    _iddia(r.returncode != 0 and "yazım YAPILMADI" in r.stderr, _ozet(r))
    _iddia(not _kalinti(s.kok, s.disari), f"geçici dosya kaldı: {_kalinti(s.kok, s.disari)}")
    _sizinti_yok(r)


# =================================================================================================
# (c) GEÇİCİ AD YARIŞI — fd tabanlı chown/chmod bağı İZLEMEZ
# =================================================================================================

#: Geçici dosya YARATILDIĞI AN adı kurban dosyaya bağ olur (ubuntu kendi dizininde bunu yapabilir). Kayıt: chown/chmod
#: çağrılarının GERÇEKTE dokunduğu inode (yol tabanlı biçimler bağı izler — kayıt da izleyerek ölçer).
_GECICI_YARISI = '''import os
_o = os.open
def _open(p, flags, mode=0o777, *, dir_fd=None):
    fd = _o(p, flags, mode, dir_fd=dir_fd)
    if flags & os.O_CREAT and os.path.basename(os.fspath(p)).startswith(".sir-rot-"):
        open(__ISARET__, "w").close()
        os.unlink(p, dir_fd=dir_fd)
        os.symlink(__KURBAN__, p, dir_fd=dir_fd)
    return fd
os.open = _open
def _yaz(islem, ino):
    with open(__KAYIT__, "a") as fh:
        fh.write("%s\\t%d\\n" % (islem, ino))
_fco, _co, _fcm, _cm = os.fchown, os.chown, os.fchmod, os.chmod
def _fchown(fd, u, g):
    _yaz("fchown", os.fstat(fd).st_ino); return _fco(fd, u, g)
def _chown(p, u, g, *, dir_fd=None, follow_symlinks=True):
    _yaz("chown", os.stat(p, dir_fd=dir_fd, follow_symlinks=follow_symlinks).st_ino)
    return _co(p, u, g, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
def _fchmod(fd, m):
    _yaz("fchmod", os.fstat(fd).st_ino); return _fcm(fd, m)
def _chmod(p, m, *, dir_fd=None, follow_symlinks=True):
    _yaz("chmod", os.stat(p, dir_fd=dir_fd, follow_symlinks=follow_symlinks).st_ino)
    return _cm(p, m, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
os.fchown, os.chown, os.fchmod, os.chmod = _fchown, _chown, _fchmod, _chmod
'''


def test_C_GECICI_AD_bag_yarisi_FD_TABANLI_chown_chmod_bagi_IZLEMEZ(tmp_path):
    """`yaz-env` (`koru koru` — sahip çözülür, chown GERÇEKTEN çağrılır). Geçici dosya yaratıldığı an adı kurbana bağ olur.
    ESKİ yol: `os.chmod(geçici)`/`os.chown(geçici)` bağı izler — kurbanın modu hedefin moduna döner (root'ta sahibi de) — ve
    `os.replace` BAĞI hedefin yerine koyar. YENİ yol: chown/chmod TANITICIYA gider (kayıtta kurbanın inode'u YOK), yerine koyma
    öncesi ölçüm adın değiştiğini görür → yazım YAPILMADI, hedef dosya bayt-eşit ve düz dosya, kurban bayt/mod aynı."""
    s = _Sahne(tmp_path)
    kurban = s.disari / "kurban"
    kurban.write_text(KURBAN + "\n", encoding="utf-8")
    kurban.chmod(0o644)
    isaret, kayit = tmp_path / "kanca_atesledi", tmp_path / "kayit.log"
    on = (_GECICI_YARISI.replace("__ISARET__", repr(str(isaret))).replace("__KURBAN__", repr(str(kurban)))
          .replace("__KAYIT__", repr(str(kayit))))
    once_k, once_h = _imza(kurban), _imza(s.env)
    r = s.kos("yaz-env", s.env, ALAN, s.dgr, "koru", "koru", "-", on=on)
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    dokunulan = {int(x.split("\t")[1]) for x in kayit.read_text().splitlines()} if kayit.exists() else set()
    _iddia(dokunulan, "chown/chmod kaydı BOŞ — sahiplik/mod hiç verilmedi mi? (pozitif kontrol)")
    _iddia(once_k[2] not in dokunulan, "chown/chmod BAĞI İZLEDİ — kurbanın inode'una dokunuldu")
    _iddia(_imza(kurban) == once_k, "kurban değişti (bayt/mod/sahip)")
    _iddia(not s.env.is_symlink() and _imza(s.env) == once_h, "hedef ezildi ya da bağa çevrildi")
    _iddia(r.returncode != 0 and "DEĞİŞTİ" in r.stderr and "yazım YAPILMADI" in r.stderr, _ozet(r))
    _iddia(not _kalinti(s.profil, s.disari), f"geçici ad kaldı: {_kalinti(s.profil, s.disari)}")
    _sizinti_yok(r)


#: Yerine koyma ANINDA ad başka bir dosyayla değişir (yerine koyma öncesi ölçümden SONRA) — yalnız yazım SONRASI `lstat`
#: yakalayabilir. `os.replace` hedefe YAZILAN dosyayı değil başka bir inode'u koyar.
_YERINE_KOYMA_YEMI = '''import os
_r = os.replace
def _sahte(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
    yem = "yem" if dst_dir_fd is not None else os.path.join(os.path.dirname(dst), "yem")
    os.close(os.open(yem, os.O_WRONLY | os.O_CREAT, 0o600, dir_fd=dst_dir_fd))
    return _r(yem, dst, src_dir_fd=dst_dir_fd, dst_dir_fd=dst_dir_fd)
os.replace = _sahte
'''


@pytest.mark.parametrize("op", ["yaz-env", "yaz-dosya"])
def test_C2_YERINE_KOYMA_yarisi_YAZIM_SONRASI_lstat_yakalar(tmp_path, op):
    """Yazım SONRASI ölçüm: hedefteki dosya yazılan inode DEĞİL → "yazım DOĞRULANAMADI", çıkış ≠ 0 (dosya yerinde bırakılır —
    bizim olmayabilir). ESKİ yolda ölçüm yoktu: çıkış 0. Geçici dosya kalmaz."""
    s = _Sahne(tmp_path)
    hedef, args, _, _ = s.argv(op)
    r = s.kos(op, *args, on=_YERINE_KOYMA_YEMI)
    _iddia(r.returncode != 0 and "DOĞRULANAMADI" in r.stderr, _ozet(r))
    _iddia(not _kalinti(s.kok), f"geçici dosya kaldı: {_kalinti(s.kok)}")
    _sizinti_yok(r)


# =================================================================================================
# (d) ROOT DİZİN HEDEFLERİ ESKİSİ GİBİ YAZILIR · sahip kuralı ölçülür
# =================================================================================================

@pytest.mark.parametrize("hal", ["root_dizininde_root_hedef", "dizin_hedefin_sahibine_ait_degil"])
def test_D_ROOT_DIZINI_hedefi_ESKISI_GIBI_yazilir_SAHIP_KURALI_olculur(tmp_path, hal):
    """Root modeli (geteuid 0). `yaz-dosya /etc/meridian/kapi_apikey 0400 <sahip>`. (root_dizininde_root_hedef) `root:root` →
    test kullanıcısı: zincirin her dizini "root" sahipli → yazılır, 0400, sahip ölçülür, çıktı SESSİZ (altın izler stdout'u
    pinler — v538 C7). (dizin_hedefin_sahibine_ait_degil) `ubuntu:ubuntu` → başka bir uid: dizinler ne root'un ne hedefin
    sahibinin → RED `sahibi uid`, dosya bayt-eşit. ESKİ yol ikinci hâlde yol tabanlı chown'u yutup çıkış 0 veriyordu."""
    s = _Sahne(tmp_path)
    uid, gid = os.getuid(), os.getgid()
    on = _root_modeli({"root": (uid, gid), "ubuntu": (uid + 4242, gid)})
    sahip = "root:root" if hal == "root_dizininde_root_hedef" else "ubuntu:ubuntu"
    once = _imza(s.dosya)
    r = s.kos("yaz-dosya", s.dosya, s.dgr, "0400", sahip, "-", on=on)
    if hal == "root_dizininde_root_hedef":
        st = s.dosya.lstat()
        _iddia(r.returncode == 0 and r.stdout == "", _ozet(r))
        _iddia(s.dosya.read_text(encoding="utf-8") == YENI + "\n" and (st.st_mode & 0o7777) == 0o400
               and (st.st_uid, st.st_gid) == (uid, gid) and st.st_ino != once[2], "root dizini hedefi ESKİSİ GİBİ yazılmadı")
    else:
        _iddia(r.returncode != 0 and "sahibi uid" in r.stderr and "yazım YAPILMADI" in r.stderr, _ozet(r))
        _iddia(_imza(s.dosya) == once, "dosya değişti")
    _iddia(not _kalinti(s.kok), f"geçici dosya kaldı: {_kalinti(s.kok)}")
    _sizinti_yok(r)


def test_D2_UCTAN_UCA_kapi_root_dizinleri_ve_koru_env_ESKISI_GIBI(tmp_path):
    """Operatörün koşacağı BİÇİM: `--kapi` (v447 sahnesi) — `/etc/meridian/kapi_apikey` 0400 YENİ değer, `.env-apisix`
    (`koru`) modu/sahibi aynı ve satırı yeni değerde; ağacın hiçbir yerinde geçici dosya kalmaz; çalışma dizini silinir."""
    kok, ortam = _sahte_ortam(tmp_path)
    apisix = kok / "opt/apisix/.env-apisix"
    apisix.chmod(0o640)
    once = apisix.stat()
    r = _kos(BETIK, ortam, "--kapi")
    _iddia(r.returncode == 0, _ozet(r))
    yeni = (kok / "etc/meridian/kapi_apikey").read_text(encoding="utf-8").strip()
    st = (kok / "etc/meridian/kapi_apikey").stat()
    _iddia(len(yeni) >= 40 and (st.st_mode & 0o7777) == 0o400, "kapi_apikey yeni değer/0400 değil")
    sonra = apisix.stat()
    _iddia((sonra.st_mode & 0o7777) == 0o640 and (sonra.st_uid, sonra.st_gid) == (once.st_uid, once.st_gid),
           "`.env-apisix` modu/sahibi KORUNMADI")
    _iddia(f"BOT_KEY_MERIDIAN='{yeni}'" in apisix.read_text(encoding="utf-8"), "`.env-apisix` satırı yazılmadı/tırnak bozuldu")
    _iddia(not _kalinti(kok) and not list(tmp_path.glob("sir-rot.*")), "geçici dosya / çalışma dizini kaldı")


# =================================================================================================
# (e) KORU — mod ve sahip KORUNUR, yazım ölçülür
# =================================================================================================

def test_E_KORU_mod_ve_sahip_KORUNUR_yeni_inode_ve_root_iken_OLCULUR(tmp_path):
    """`yaz-env koru koru` hermes profilinde (0640) root modeliyle: mod 0640 ve sahip AYNEN, içerik yeni değerde (öteki satır
    bayt-eşit), inode YENİ (atomik yerine koyma), çıktı SESSİZ. `koru` ama dosya YOK → eski ileti ("mod=koru ama dosya YOK"),
    hiçbir dosya doğmaz."""
    s = _Sahne(tmp_path)
    once = s.env.stat()
    on = _root_modeli({})
    r = s.kos("yaz-env", s.env, ALAN, s.dgr, "koru", "koru", "-", on=on)
    sonra = s.env.lstat()
    _iddia(r.returncode == 0 and r.stdout == "", _ozet(r))
    _iddia((sonra.st_mode & 0o7777) == 0o640 and (sonra.st_uid, sonra.st_gid) == (once.st_uid, once.st_gid)
           and sonra.st_ino != once.st_ino, "koru mod/sahip korunmadı ya da yerine koyma atomik değil")
    _iddia(s.env.read_text(encoding="utf-8") == f"HERMES_HOME=/home/ubuntu/.hermes/profiles/sef\n{ALAN}={YENI}\n",
           "içerik beklenen değil")
    yok = s.profil / ".env-yok"
    r2 = s.kos("yaz-dosya", yok, s.dgr, "koru", "koru", "-")
    _iddia(r2.returncode != 0 and "mod=koru ama dosya YOK" in r2.stderr and not os.path.lexists(yok), _ozet(r2))
    _iddia(not _kalinti(s.kok), f"geçici dosya kaldı: {_kalinti(s.kok)}")


# =================================================================================================
# (f) ÖN-DENETİM — bağlı / gevşek hedef rotasyonu HİÇ BAŞLATMAZ (yarım rotasyon yok)
# =================================================================================================

@pytest.mark.parametrize("hal", ["hedef_bag", "dizin_bag", "grup_yazar"])
def test_F_ON_DENETIM_bagli_ya_da_gevsek_hedef_ROTASYONU_HIC_BASLATMAZ(tmp_path, hal):
    """`--tenant` (referans + üç sohbet profili `.env`i, `karne` SON yazılır). `karne/.env` bağ / `profiles/karne` bağ /
    `profiles/karne` 0775. Yazım anı ret TEK BAŞINA referansı ve ilk iki profili yazıp karne'de DURURDU (yarım rotasyon);
    ön-denetim aynı `_hedef_ac`ı yazımdan ÖNCE koşar → çıkış 1, "hedef REDDEDİLDİ" + yol, sahte kökte HİÇBİR dosya değişmez,
    yedek yok, bağın hedefi bayt-eşit."""
    kok, ortam = _sahte_ortam(tmp_path)
    profil = kok / "home/ubuntu/.hermes-botlar/profiles/karne"
    disari = tmp_path / "disari"
    disari.mkdir(mode=0o755)
    if hal == "hedef_bag":
        kurban = disari / "kurban.env"
        (profil / ".env").rename(kurban)
        (profil / ".env").symlink_to(kurban)
        neden = "SEMBOLİK BAĞ"
    elif hal == "dizin_bag":
        gercek = disari / "karne_gercek"
        profil.rename(gercek)
        profil.symlink_to(gercek, target_is_directory=True)
        neden = "SEMBOLİK BAĞ"
    else:
        profil.chmod(0o775)
        neden = "YAZABİLİR"
    once_k, once_d = _agac_imzasi(kok), _agac_imzasi(disari)
    r = _kos(BETIK, ortam, "--tenant")
    sonra_k = {k: v for k, v in _agac_imzasi(kok).items() if not k.startswith(".sahte")}
    _iddia(sonra_k == {k: v for k, v in once_k.items() if not k.startswith(".sahte")}, "sahte kökte bir dosya DEĞİŞTİ")
    _iddia(_agac_imzasi(disari) == once_d, "bağın hedefi değişti")
    _iddia(not list((kok / "root").glob("sir-yedek-*")), "yedek alındı — rotasyon başlamıştı")
    _iddia(r.returncode == 1 and "hedef REDDEDİLDİ: /home/ubuntu/.hermes-botlar/profiles/karne/.env" in r.stderr
           and neden in r.stderr and "HİÇBİR ŞEY yazılmadı" in r.stderr, _ozet(r))


# =================================================================================================
# (g) ÇAPA — iki güvenilir çapa (kök · yardımcının kendi dizini); dışı RED
# =================================================================================================

def test_G_CAPA_disi_hedef_RED_islik_ciktisi_YAZILIR(tmp_path):
    """Çalışma dizini çıktısı (`cikar` → `islik/eski`) yazılır (ikinci çapa: yardımcının KENDİ dizini). Kökün de çalışma
    dizininin de DIŞINDAKİ bir hedef (`disari/x`) RED — "DIŞINDA", dosya doğmaz. ESKİ yol çapa bilmiyordu: çıkış 0."""
    s = _Sahne(tmp_path)
    cikti = s.islik / "eski"
    r = s.kos("cikar", "env", s.env, ALAN, "-", cikti)
    _iddia(r.returncode == 0 and cikti.read_text(encoding="utf-8") == ESKI_ENV + "\n"
           and (cikti.stat().st_mode & 0o7777) == 0o600, _ozet(r))
    dis = s.disari / "x"
    r2 = s.kos("yaz-dosya", dis, s.dgr, "0600", "-", "-")
    _iddia(r2.returncode != 0 and "DIŞINDA" in r2.stderr and not os.path.lexists(dis), _ozet(r2))
    _iddia(not _kalinti(s.islik, s.disari), "geçici dosya kaldı")
    _sizinti_yok(r)
    _sizinti_yok(r2)


def test_H_tek_govde_STATIK_rotasyon_ve_tohumlama_AYNI_zincir_fonksiyonu():
    """Tek-kaynak (brief: "kopya yazma"): `_dizin_ac` yardımcıda TEK tanımdır ve hem tohumlamanın (`dizin-denetle` ·
    `tohumla-env`) hem rotasyonun (`_hedef_ac`) zinciri ondan geçer; yazım gövdesi (`_gecici_yaz` + `_yazim_kusurlari`) iki
    yolda ortaktır; yol tabanlı `os.chown(`/`os.chmod(`/`tempfile.mkstemp` yardımcıda YOKTUR."""
    ham = BETIK.read_text(encoding="utf-8")
    bas = ham.index("<<'PY_SON'\n")
    yardimci = ham[bas:ham.index("\nPY_SON\n", bas)]
    _iddia(yardimci.count("def _dizin_ac(") == 1 and yardimci.count("def _gecici_yaz(") == 1
           and yardimci.count("def _yazim_kusurlari(") == 1, "zincir/yazım gövdesi TEK tanım değil")
    hedef_ac = yardimci[yardimci.index("def _hedef_ac("):]
    hedef_ac = hedef_ac[:hedef_ac.index("\ndef ", 1)]
    _iddia("_dizin_ac(" in hedef_ac, "rotasyon zinciri `_dizin_ac`tan geçmiyor")
    yeni = yardimci[yardimci.index("def _yeni_dosya_yaz("):]
    yeni = yeni[:yeni.index("\ndef ", 1)]
    _iddia("_gecici_yaz(" in yeni and "_yazim_kusurlari(" in yeni, "tohumlama yazımı ortak gövdeden geçmiyor")
    for yasak in ("os.chown(", "os.chmod(", "tempfile.mkstemp", "import tempfile"):
        _iddia(yasak not in yardimci, f"yardımcıda yol tabanlı yazım kaldı: {yasak}")
    for cagri in ("os.replace(", "os.link("):
        satirlar = [s for s in yardimci.splitlines() if cagri in s and not s.lstrip().startswith("#")]
        _iddia(bool(satirlar) and all("dst_dir_fd=" in s for s in satirlar),
               f"`{cagri}` dizin tanıtıcısız çağrılıyor (yol tabanlı): {satirlar}")

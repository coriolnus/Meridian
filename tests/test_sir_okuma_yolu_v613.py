"""test_sir_okuma_yolu_v613.py — TSK-262: sır rotasyon aracının OKUMA yolu fd çekirdeğine (FIFO askısı · bağ izleme) + TSK-261
yeniden incelemesinin iki Minörü (N1 `alan-farki` ad sözleşmesi · N2 yarım ön yedek).

NUMARA: Rol-1 rezervasyonu (brief `.superpowers/sdd/tsk262/brief.md`); `ls tests | grep v613` boş — bu worktree, ana checkout ve
bütün `.claude/worktrees/*/tests` (ölçüldü 2026-10-02; en yüksek v612).

SINIF (CWE-59 / CWE-400). TSK-260 yardımcının YAZIM yolunu, TSK-261 KOPYA yollarını fd çekirdeğine bağladı (`_hedef_ac` ·
`_tanitictan_oku` — `O_NOFOLLOW|O_NONBLOCK`, fstat normal dosya + inode). OKUMA yolu çıplak `_oku(yol)` = `open(yol)` idi: bağı
İZLER (root bağın HEDEFİNİ okur; içerik kıyasa ya da 0700 işliğe girer) ve FIFO'da bir yazarı SÜRESİZ bekler. Ubuntu sahipli hedef
dizinlerinde (hermes `.env`leri, `~/.hermes-botlar`, `/opt/meridian/state`) dosyayı FIFO'ya çeviren biri `--envanter`i, ön-denetimi
(`alan-var … tek`) ve rotasyonu hiç başlatmaz (inceleme M2).

YENİ SÖZLEŞME — `_oku` okuma yolunun TEK gövdesi: (1) `lstat` — YOK → `FileNotFoundError` (eski kovalar: YOK · DOSYA YOK ·
REFERANS YOK), normal dosya DEĞİL → `OkumaReddi` (tür ADIYLA: SEMBOLİK BAĞ · FIFO · SOKET · AYGIT · DİZİN), hiç AÇILMAZ; (2)
`_hedef_ac(koru, koru)` — zincir yazımın kuralıyla ("ZİNCİR: …"); (3) `_tanitictan_oku(okuma=True)` — `O_NOFOLLOW|O_NONBLOCK`,
fstat normal dosya + aynı inode (yarışta FIFO'ya/bağa çevrilen dosya). Hüküm basan işlemler `OKUNAMADI (<tür>)` der (`esit` taraf
ADIYLA: `REFERANS OKUNAMADI (<tür>)`); çıkışla biten işlemler (`cikar` · `pgpass` · `dsn-uc` · `alanlar` · `alan-farki` · değer
dosyası) adlı iletiyle (yol + tür) durur. Değer hiçbir yerde basılmaz.

N1 — `alan-farki` adı yalnız aracın ad sözleşmesiyle basar (`^[A-Z][A-Z0-9_]*$` — kabuktaki `_aranan_adlar`ın deseni); tırnağı
satırda kapanmayan değerin DEVAM satırı değerdir, ad DEĞİL; sözleşme dışı/adsız farklı satırlar YALNIZ sayıyla ("+ adsız N satır").
N2 — yarıda kalan yedek `.yarim` adına taşınır (girdi kalıbı reddeder); `--geri-al`ın ön yedeği `KOKEN` taşır, envanterin yedek
listesi onu "ÖN YEDEK" diye ayırır.

DÜZELTME TURU 1 (güvenlik incelemesi `.superpowers/sdd/tsk262/review.md`, 2026-10-02): I1 — `alan-farki` adı BİÇİMDEN BAĞIMSIZ
kuralla basar (iki tarafta da var ve farklı · ya da aranan ad / sır-adı soneki; D1 beş biçim · D7 · D8); M1 — inode eşitliği
denetimi çivili (A3: açılışta normal dosya takası); M3 — `esitle` kanıtı okunamayan satırı EŞİT saymaz (F3); K1 (dosya içi kısmi) —
betik `cd /` + mutlak betik dizini, her yorumlayıcı `-I` (K1a–K1d; root sahipli kurulum yeri ayrı kalem TSK-265).

ÇIKTI DİSİPLİNİ: iddialar bool'a indirgenir (`_iddia`); değerler SAHTEdir ve hiçbir çıktıda görünmemelidir. Askı KIRMIZIDIR: alt
süreç zaman aşımıyla koşar (`_yk_sure` → None), asla sonsuz beklemez.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import re
import signal
import stat
import subprocess
import sys

import pytest

from tests.test_sir_kopya_yolu_v611 import (GIRDI_OR, _eskit, _fonksiyon, _imzalar, _kapi_sahnesi, _satir_sonrasi,
                                            _sudo_kancasi, _yardimci_metni, _yedekler, _yk_sure)
from tests.test_sir_rotasyon_v447 import (BAYAT_OR, BETIK, ESKI, GLOBAL_HERMES, KOK_DEPO, YENI_NOUS, YENI_OR, _global_ayir,
                                          _sahte_ortam)
from tests.test_sir_yazim_yolu_v609 import ALAN, ESKI_DOSYA, ESKI_ENV, YENI, _iddia, _imza, _Sahne

IZ = "SAHTE-V613-IZ-0001"            # bağın HEDEFİNDEKİ işaret — hiçbir çıktıda/kıyasta görünmemeli
ESKI_JSON = "SAHTE-V613-JSON-0002"
_DEGERLER = (*ESKI.values(), YENI_NOUS, YENI_OR, YENI, ESKI_ENV, ESKI_DOSYA, IZ, ESKI_JSON, BAYAT_OR)
SURE = 20.0                          # askı tavanı (v611 C emsali — yük-bağımsız; başarı yolu < 1 s)


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _maskeli(metin: str) -> str:
    for d in _DEGERLER:
        metin = metin.replace(d, "<SAHTE-DEGER>")
    return metin


def _ozet(r: subprocess.CompletedProcess | None) -> str:
    if r is None:
        return "ASKIDA KALDI (zaman aşımı)"
    return f"çıkış {r.returncode}\n--- stdout ---\n{_maskeli(r.stdout)[-3000:]}\n--- stderr ---\n{_maskeli(r.stderr)[-3000:]}"


def _sizinti_yok(r: subprocess.CompletedProcess) -> None:
    _iddia(not any(d in r.stdout + r.stderr for d in _DEGERLER), "bir SAHTE değer çıktıya düştü")


def _kos_sure(ortam: dict, *args: str, girdi: str = "", sure: float = 180.0, cwd: pathlib.Path | None = None,
              betik: str | None = None) -> subprocess.CompletedProcess | None:
    """Betiği operatörün biçimiyle koşar (v447 `_kos`) — ama ZAMAN AŞIMIYLA: okuma askısı KIRMIZI olmalı, asılı test değil.
    Askıda süreç GRUBU öldürülür: `subprocess.run(timeout=)` yalnız `bash`i öldürür, `$( )` alt kabuğu ve FIFO'da bekleyen
    yardımcı (sudo şimi → python) yetim kalırdı (ölçüldü 2026-10-02: taban betiğe karşı RED koşumu iki yetim bıraktı)."""
    p = subprocess.Popen(["bash", betik or str(BETIK), *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, env=ortam, start_new_session=True,
                         cwd=str(cwd) if cwd else None)
    try:
        out, err = p.communicate(girdi, timeout=sure)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.communicate()
        return None
    return subprocess.CompletedProcess(p.args, p.returncode, out, err)


def _dizin_0755(*dizinler: pathlib.Path) -> None:
    for d in dizinler:
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o755)


class _OkumaSahnesi(_Sahne):
    """v609 sahnesi (+ motor deposu JSON'u, kıyas için ikinci `.env`/JSON, kök İÇİNDE bir bağ hedefi)."""

    def __init__(self, tmp_path: pathlib.Path) -> None:
        super().__init__(tmp_path)
        durum = self.kok / "opt/meridian/state"
        _dizin_0755(self.kok / "opt", self.kok / "opt/meridian", durum)
        self.json = durum / "secrets.json"
        self.json.write_text(json.dumps({"NOUS_API_KEY": ESKI_JSON, "ALPACA_API_KEY": ESKI_JSON}) + "\n", encoding="utf-8")
        self.json_yedek = self.kok / "etc/meridian/secrets_yedek.json"
        self.json_yedek.write_text(self.json.read_text(encoding="utf-8"), encoding="utf-8")
        self.diger = self.kok / "etc/meridian/diger.env"
        self.diger.write_text(self.env.read_text(encoding="utf-8"), encoding="utf-8")
        # Bağın hedefi kökün İÇİNDE (üretimde çapa `/`dir): ağaç-dışı bir hedef çapa katmanına ("DIŞINDA") da takılır ve bağ
        # katmanını tek başına ölçmezdi (v611 B1 emsali).
        self.kurban = self.kok / "etc/meridian/gizli_iz"

    def kurban_kur(self, tur: str) -> pathlib.Path:
        """Bağın hedefi — İZLENSEYDİ okuma işlemini BAŞARIYA götürecek içerikle (işaret `IZ`)."""
        icerik = {
            "env": f"{ALAN}={IZ}\nIZ_ALANI={IZ}\n",
            "dosya": f"{IZ}\n",
            "url": f"postgresql://iz_kullanici:{IZ}@127.0.0.1:5432/iz_db\n",
            "json": json.dumps({"NOUS_API_KEY": IZ, "IZ_ALANI": IZ}) + "\n",
        }[tur]
        self.kurban.write_text(icerik, encoding="utf-8")
        self.kurban.chmod(0o644)
        return self.kurban

    def islem(self, ad: str) -> tuple[pathlib.Path, str, tuple, str]:
        """ad → (bozulacak yol, yolun içerik türü, argümanlar, kip). kip: `hukum` (stdout `OKUNAMADI (<tür>)`, çıkış 0) ·
        `referans` (`REFERANS OKUNAMADI (<tür>)`) · `cikis` (çıkış ≠ 0, stderr'de adlı ret: yol + tür)."""
        c = self.islik / "cikti"
        return {
            "alan-var": (self.env, "env", ("alan-var", self.env, ALAN), "hukum"),
            "alan-var-tek": (self.env, "env", ("alan-var", self.env, ALAN, "tek"), "hukum"),
            "alan-var-tek-dolu": (self.env, "env", ("alan-var", self.env, ALAN, "tek", "dolu"), "hukum"),
            "var-env": (self.env, "env", ("var", "env", self.env, ALAN), "hukum"),
            "var-dosya": (self.dosya, "dosya", ("var", "dosya", self.dosya, "-"), "hukum"),
            "var-url": (self.url, "url", ("var", "url", self.url, "-"), "hukum"),
            "esit-kopya": (self.env, "env", ("esit", "dosya", self.dosya, "-", "-", "env", self.env, ALAN, "-"), "hukum"),
            "esit-referans": (self.env, "env", ("esit", "env", self.env, ALAN, "-", "dosya", self.dosya, "-", "-"),
                              "referans"),
            "json-ad-var": (self.json, "json", ("json-ad-var", self.json, "NOUS_API_KEY"), "hukum"),
            "alanlar": (self.env, "env", ("alanlar", self.env), "cikis"),
            "cikar-env": (self.env, "env", ("cikar", "env", self.env, ALAN, "-", c), "cikis"),
            "cikar-dosya": (self.dosya, "dosya", ("cikar", "dosya", self.dosya, "-", "-", c), "cikis"),
            "cikar-url": (self.url, "url", ("cikar", "url", self.url, "-", "-", c), "cikis"),
            "dsn-uc": (self.url, "url", ("dsn-uc", self.url), "cikis"),
            "pgpass": (self.url, "url", ("pgpass", c, self.url), "cikis"),
            "alan-farki-yedek": (self.env, "env", ("alan-farki", "env", self.env, self.diger), "cikis"),
            "alan-farki-guncel": (self.env, "env", ("alan-farki", "env", self.diger, self.env), "cikis"),
            "alan-farki-api": (self.json, "json", ("alan-farki", "api", self.json_yedek, self.json), "cikis"),
            "deger-dosyasi": (self.dgr, "dosya", ("yaz-dosya", self.dosya, self.dgr, "0400", "root:root", "-"), "cikis"),
        }[ad]


OKUMA_ISLEMLERI = ("alan-var", "alan-var-tek", "alan-var-tek-dolu", "var-env", "var-dosya", "var-url", "esit-kopya",
                   "esit-referans", "json-ad-var", "alanlar", "cikar-env", "cikar-dosya", "cikar-url", "dsn-uc", "pgpass",
                   "alan-farki-yedek", "alan-farki-guncel", "alan-farki-api", "deger-dosyasi")


def _adli_ret(s: _OkumaSahnesi, r: subprocess.CompletedProcess | None, yol: pathlib.Path, kip: str, tur: str) -> None:
    """Askı YOK + işlemin sözleşmesine göre ADLI ret: hüküm satırı TAM (`OKUNAMADI (<tür>)`) ya da çıkış ≠ 0 ve stderr'de
    `okuma REDDİ: <yol>: <tür>`. Hiçbir çıktı dosyası doğmaz, hedef (değer dosyası işleminin) bayt-eşit kalır."""
    _iddia(r is not None, f"okuma ASKIDA KALDI ({SURE} s zaman aşımı) — O_NONBLOCK/tür denetimi yok")
    if kip in ("hukum", "referans"):
        bek = f"{'REFERANS ' if kip == 'referans' else ''}OKUNAMADI ({tur}"
        _iddia(r.returncode == 0 and r.stdout.strip().startswith(bek), f"beklenen hüküm '{bek}…)'\n{_ozet(r)}")
    else:
        _iddia(r.returncode != 0 and r.stdout.strip() == "" and f"okuma REDDİ: {yol}: {tur}" in r.stderr,
               f"beklenen adlı ret 'okuma REDDİ: <yol>: {tur}'\n{_ozet(r)}")
    _iddia(not (s.islik / "cikti").exists(), "reddedilen okumadan bir çıktı dosyası DOĞDU")
    _sizinti_yok(r)


#: YARIŞ KANCASI — hedefin dizin tanıtıcısına göre AÇILIŞ anında (`_tanitictan_oku`, denetimlerden SONRA) dosyayı değiştirir.
#: Kanca uygulamadan BAĞIMSIZ bir olaya bağlıdır (hedefin adı + dizininin inode'u + O_CREAT/O_DIRECTORY olmayan açılış).
def _yaris_kancasi(yol: pathlib.Path, isaret: pathlib.Path, eylem: str, sonra: str = "") -> str:
    return (
        "import os\n_o = os.open\n"
        f"_DIZIN = os.stat({str(yol.parent)!r}).st_ino\n"
        "def _open(p, flags, mode=0o777, *, dir_fd=None):\n"
        f"    if (dir_fd is not None and p == {yol.name!r} and not flags & (os.O_CREAT | os.O_DIRECTORY)\n"
        f"            and os.fstat(dir_fd).st_ino == _DIZIN and not os.path.exists({str(isaret)!r})):\n"
        f"        open({str(isaret)!r}, 'w').close()\n"
        f"        os.unlink({str(yol)!r})\n"
        f"        {eylem}\n"
        "        fd = _o(p, flags, mode, dir_fd=dir_fd)\n"
        f"        {sonra or 'pass'}\n"
        "        return fd\n"
        "    return _o(p, flags, mode, dir_fd=dir_fd)\n"
        "os.open = _open\n")


# =================================================================================================
# A) FIFO — her okuma işlemi FIFO hedefte ASKIDA KALMAZ, tür ADIYLA reddeder
# =================================================================================================

@pytest.mark.parametrize("ad", OKUMA_ISLEMLERI)
def test_A1_FIFO_hedef_ASKIDA_KALMAZ_FIFO_adiyla_reddedilir(tmp_path, ad):
    """Hedef ÖNCEDEN bir FIFO (ubuntu kendi dizininde `.env`ini FIFO'ya çevirdi). ESKİ yol `open()` bir yazarı SÜRESİZ bekler
    (root `--envanter`/ön-denetim/rotasyon asılır). YENİ yol: `lstat` türü görür, dosya HİÇ AÇILMAZ — `OKUNAMADI (FIFO)` ya da
    adlı çıkış (yol + FIFO); zaman aşımı YOK, FIFO yerinde, değer basılmaz."""
    s = _OkumaSahnesi(tmp_path)
    yol, _tur, args, kip = s.islem(ad)
    once = _imza(s.dosya)
    yol.unlink()
    os.mkfifo(yol, 0o600)
    r = _yk_sure(s.yardimci, *args, kok=s.kok, sure=SURE)
    _adli_ret(s, r, yol, kip, "FIFO")
    _iddia(stat.S_ISFIFO(yol.lstat().st_mode), "FIFO yerinde değil")
    if ad == "deger-dosyasi":
        _iddia(_imza(s.dosya) == once, "değer dosyası okunamadan hedef YAZILDI")


@pytest.mark.parametrize("ad", OKUMA_ISLEMLERI)
def test_A2_YARIS_acilis_aninda_FIFOya_cevrilen_dosya_ASKIDA_KALMAZ(tmp_path, ad):
    """Denetimler (lstat · zincir · hedef lstat) NORMAL dosya görür; açılış ANINDA dosya FIFO'ya çevrilir (kanca). Tek savunma
    açılışın kendisidir: `O_NONBLOCK` (yoksa açılış yazarı SÜRESİZ bekler → zaman aşımı) ve tanıtıcının `fstat`ı (`S_ISREG` —
    yoksa tür adı FIFO OLMAZ). Beklenen: kanca ATEŞLENDİ (pozitif kontrol), `OKUNAMADI (FIFO)` / adlı çıkış."""
    s = _OkumaSahnesi(tmp_path)
    yol, _tur, args, kip = s.islem(ad)
    isaret = tmp_path / "kanca_atesledi"
    on = _yaris_kancasi(yol, isaret, f"os.mkfifo({str(yol)!r}, 0o600)")
    r = _yk_sure(s.yardimci, *args, kok=s.kok, on=on, sure=SURE)
    _iddia(isaret.exists(), f"yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)\n{_ozet(r)}")
    _adli_ret(s, r, yol, kip, "FIFO")


@pytest.mark.parametrize("ad", OKUMA_ISLEMLERI)
def test_A3_YARIS_acilis_aninda_BASKA_NORMAL_dosyayla_takas_DEGISTI_ile_reddedilir(tmp_path, ad):
    """TSK-262 düzeltme turu 1 (inceleme M1, `scratchpad/tsk262-inceleme/inode_sonda.log`): denetimler (lstat · zincir · hedef
    lstat) asıl dosyayı ölçer; AÇILIŞ ANINDA hedef, aynı dizine taşınan BAŞKA bir NORMAL dosyayla takas edilir (kanca). FIFO/bağ
    değil — tür denetimi onu geçirir; tek savunma tanıtıcının inode'unun denetlenenle EŞİTLİĞİDİR (takas edilen sert bağa karşı da
    tek savunma). Beklenen: `OKUNAMADI (DEĞİŞTİ (yarış))` / adlı çıkış; takas edilen dosyanın içeriği (`IZ`) ve adları
    (`IZ_ALANI` · `iz_kullanici`) çıktıda YOK; değer dosyası işleminde hedef bayt-eşit. Kanca pozitif kontrol taşır."""
    s = _OkumaSahnesi(tmp_path)
    yol, tur, args, kip = s.islem(ad)
    takas = s.kurban_kur(tur)
    if ad.startswith("esit"):
        s.dosya.chmod(0o600)
        s.dosya.write_text(IZ + "\n", encoding="utf-8")     # takas edilen okunsaydı EŞİT derdi
    once = _imza(s.dosya)
    isaret = tmp_path / "kanca_atesledi"
    on = _yaris_kancasi(yol, isaret, f"os.rename({str(takas)!r}, {str(yol)!r})")
    r = _yk_sure(s.yardimci, *args, kok=s.kok, on=on, sure=SURE)
    _iddia(isaret.exists(), f"yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)\n{_ozet(r)}")
    _adli_ret(s, r, yol, kip, "DEĞİŞTİ (yarış)")
    _iddia("IZ_ALANI" not in r.stdout + r.stderr and "iz_kullanici" not in r.stdout + r.stderr,
           "takas edilen dosyadan okunan bir ad çıktıya düştü")
    if ad == "deger-dosyasi":
        _iddia(_imza(s.dosya) == once, "takas edilen değer dosyası OKUNDU — hedef yazıldı")


# =================================================================================================
# B) BAĞ — bağın hedefi OKUNMAZ (işaret ne çıktıda ne kıyasta), bağın hedefi AÇILMAZ
# =================================================================================================

@pytest.mark.parametrize("ad", OKUMA_ISLEMLERI)
def test_B1_BAG_hedefin_icerigi_OKUNMAZ_SEMBOLIK_BAG_adiyla_reddedilir(tmp_path, ad):
    """Hedef, kökün İÇİNDEKİ bir dosyaya bağ; bağın hedefi `IZ` işaretini taşır ve İZLENSEYDİ işlemi başarıya götürürdü
    (`var` → VAR · `esit` → EŞİT [referans/kopya değeri `IZ`] · `alanlar` → `IZ_ALANI` · `cikar`/`pgpass` → `IZ` çıktıya ·
    `dsn-uc` → `iz_kullanici` · `alan-farki` → `IZ_ALANI` · değer dosyası → `IZ` hedefe). YENİ: `OKUNAMADI (SEMBOLİK BAĞ)` / adlı
    çıkış; `IZ` ne stdout/stderr'de ne işlikte ne hedefte; bağ yerinde."""
    s = _OkumaSahnesi(tmp_path)
    yol, tur, args, kip = s.islem(ad)
    kurban = s.kurban_kur(tur)
    if ad.startswith("esit"):
        s.dosya.chmod(0o600)
        s.dosya.write_text(IZ + "\n", encoding="utf-8")     # izlenseydi EŞİT derdi
    once = _imza(s.dosya)
    yol.unlink()
    yol.symlink_to(kurban)
    r = _yk_sure(s.yardimci, *args, kok=s.kok, sure=SURE)
    _adli_ret(s, r, yol, kip, "SEMBOLİK BAĞ")
    _iddia("IZ_ALANI" not in r.stdout + r.stderr and "iz_kullanici" not in r.stdout + r.stderr,
           "bağın HEDEFİNDEN okunan bir ad/alan çıktıya düştü")
    _iddia(not any(IZ.encode() in p.read_bytes() for p in s.islik.rglob("*") if p.is_file() and not p.is_symlink()),
           "işaret İŞLİĞE kopyalandı")
    if ad == "deger-dosyasi":
        _iddia(_imza(s.dosya) == once, "bağlı değer dosyası İZLENDİ — hedef yazıldı")
    _iddia(yol.is_symlink() and os.readlink(yol) == str(kurban), "bağa dokunuldu")


@pytest.mark.parametrize("ad", ["alan-var-tek", "var-env", "esit-kopya", "alanlar", "cikar-env", "alan-farki-guncel"])
def test_B2_ZINCIRDE_BAG_hedefin_dizini_bag_ZINCIR_adiyla_reddedilir(tmp_path, ad):
    """Hedefin DİZİNİ (`profiles/sef`) kökün içindeki başka bir dizine bağ; oradaki `.env` `IZ` taşır. `lstat` son bileşeni
    izlemez ama ara bileşeni İZLER (normal dosya görür) — ret yazımın zincir kuralından gelir (`_hedef_ac` → `_dizin_ac`,
    `O_NOFOLLOW|O_DIRECTORY` bileşen bileşen): `OKUNAMADI (ZİNCİR: <bileşen>: SEMBOLİK BAĞ …)` / adlı çıkış; `IZ` görünmez."""
    s = _OkumaSahnesi(tmp_path)
    yol, _tur, args, kip = s.islem(ad)
    gercek = s.kok / "etc/meridian/sef_gercek"
    _dizin_0755(gercek)
    (gercek / ".env").write_text(f"{ALAN}={IZ}\nIZ_ALANI={IZ}\n", encoding="utf-8")
    s.dosya.chmod(0o600)
    s.dosya.write_text(IZ + "\n", encoding="utf-8")         # `esit-kopya` izleseydi EŞİT derdi
    for p in s.profil.iterdir():
        p.unlink()
    s.profil.rmdir()
    s.profil.symlink_to(gercek, target_is_directory=True)
    r = _yk_sure(s.yardimci, *args, kok=s.kok, sure=SURE)
    _adli_ret(s, r, yol, kip, "ZİNCİR")
    _iddia("SEMBOLİK BAĞ" in r.stdout + r.stderr and "IZ_ALANI" not in r.stdout + r.stderr, _ozet(r))


@pytest.mark.parametrize("ad", ["alan-var-tek", "esit-kopya", "alanlar", "cikar-env"])
def test_B3_YARIS_acilis_aninda_BAGA_cevrilen_dosya_bagin_hedefini_ACMAZ(tmp_path, ad):
    """Denetimlerden SONRA, açılış ANINDA hedef bir FIFO'ya BAĞ olur (kanca). `O_NOFOLLOW` açılışı ELOOP ile düşürür: bağın
    hedefi HİÇ AÇILMAZ (`OKUNAMADI (SEMBOLİK BAĞ)`). `O_NOFOLLOW` olmasaydı açılış bağı izler ve FIFO'yu okuma ucundan açardı —
    inode denetimi içeriği yine reddeder, ama AÇILIŞIN yan etkisi gerçekleşmiş olurdu (aygıt/FIFO açmak bir olaydır: bekleyen
    yazarı serbest bırakır, bazı aygıtlar açılışta davranır). Ölçüm: kanca açılıştan hemen sonra FIFO'yu YAZMA ucundan
    `O_NONBLOCK` ile açmayı dener — ancak bir OKUYAN varsa başarır (yoksa ENXIO)."""
    s = _OkumaSahnesi(tmp_path)
    yol, _tur, args, kip = s.islem(ad)
    boru = s.kok / "etc/meridian/boru"
    os.mkfifo(boru, 0o600)
    isaret, acildi = tmp_path / "kanca_atesledi", tmp_path / "boru_acildi"
    sonra = (f"try:\n            _w = _o({str(boru)!r}, os.O_WRONLY | os.O_NONBLOCK)\n"
             "        except OSError:\n            _w = None\n"
             f"        if _w is not None:\n            os.close(_w)\n            open({str(acildi)!r}, 'w').close()")
    on = _yaris_kancasi(yol, isaret, f"os.symlink({str(boru)!r}, {str(yol)!r})", sonra)
    r = _yk_sure(s.yardimci, *args, kok=s.kok, on=on, sure=SURE)
    _iddia(isaret.exists(), f"yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)\n{_ozet(r)}")
    _iddia(not acildi.exists(), "bağın HEDEFİ (FIFO) okuma ucundan AÇILDI — açılış bağı izledi (O_NOFOLLOW yok)")
    _adli_ret(s, r, yol, kip, "SEMBOLİK BAĞ")


# =================================================================================================
# C) DÜZENLİ DOSYA — hüküm sözleşmesi AYNEN (YOK · DOSYA YOK · REFERANS YOK · ALAN YOK · ÇİFT SATIR · VAR · BOŞ · OKUNAMADI)
# =================================================================================================

def test_C1_DUZENLI_dosyada_HUKUM_SOZLESMESI_AYNEN(tmp_path):
    """Okuma yolu değişti, sözleşme DEĞİŞMEDİ: aynı girdide eski kovalar aynı metinle döner (çağıranlar bu metinleri `case` ile
    ayırır — v447/v604/v609/v611 uçtan uca ölçer; burası yardımcı katmanında tablo)."""
    s = _OkumaSahnesi(tmp_path)
    m = s.kok / "etc/meridian"
    (m / "cift.env").write_text(f"{ALAN}=a\n{ALAN}=b\n", encoding="utf-8")
    (m / "bos.env").write_text(f"{ALAN}=\n", encoding="utf-8")
    (m / "bos_dosya").write_text("\n", encoding="utf-8")
    (m / "esit.env").write_text(f"X=1\n{ALAN}={ESKI_DOSYA}\n", encoding="utf-8")
    (m / "bozuk.json").write_text("{bozuk\n", encoding="utf-8")
    yok = m / "yok.env"
    beklenen = [
        (("alan-var", s.env, ALAN), "VAR"), (("alan-var", s.env, "YOK_ALAN"), "YOK"), (("alan-var", yok, ALAN), "YOK"),
        (("alan-var", s.env, ALAN, "tek"), "VAR"), (("alan-var", s.env, "YOK_ALAN", "tek"), "ALAN YOK"),
        (("alan-var", m / "cift.env", ALAN, "tek"), "ÇİFT SATIR (2)"), (("alan-var", yok, ALAN, "tek"), "DOSYA YOK"),
        (("alan-var", m / "bos.env", ALAN, "tek", "dolu"), "BOŞ"), (("alan-var", s.env, ALAN, "tek", "dolu"), "VAR"),
        (("var", "env", s.env, ALAN), "VAR"), (("var", "dosya", s.dosya, "-"), "VAR"), (("var", "url", s.url, "-"), "VAR"),
        (("var", "dosya", m / "bos_dosya", "-"), "BOŞ"), (("var", "dosya", yok, "-"), "YOK"),
        (("var", "env", s.env, "YOK_ALAN"), "ALAN YOK"), (("var", "env", m / "cift.env", ALAN), "ÇİFT SATIR (2)"),
        (("esit", "dosya", s.dosya, "-", "-", "env", m / "esit.env", ALAN, "-"), "EŞİT"),
        (("esit", "dosya", s.dosya, "-", "-", "env", s.env, ALAN, "-"), "AYRI"),
        (("esit", "dosya", s.dosya, "-", "-", "env", yok, ALAN, "-"), "YOK"),
        (("esit", "env", yok, ALAN, "-", "dosya", s.dosya, "-", "-"), "REFERANS YOK"),
        (("esit", "dosya", s.dosya, "-", "-", "env", m / "cift.env", ALAN, "-"), "ÇİFT SATIR (2)"),
        (("json-ad-var", s.json, "NOUS_API_KEY"), "VAR"), (("json-ad-var", s.json, "YOK_AD"), "YOK"),
        (("json-ad-var", m / "bozuk.json", "NOUS_API_KEY"), "OKUNAMADI"),
        (("alanlar", s.env), f"HERMES_HOME\n{ALAN}"), (("alanlar", yok), ""),
        (("dsn-uc", s.url), "127.0.0.1 5432 hindsight hindsight"),
        (("alan-farki", "env", s.env, s.diger), "AYNI"),
        (("alan-farki", "api", s.json_yedek, s.json), "AYNI"),
    ]
    for args, bek in beklenen:
        r = _yk_sure(s.yardimci, *args, kok=s.kok, sure=SURE)
        _iddia(r is not None and r.returncode == 0 and r.stdout.strip() == bek,
               f"{args[0]} {[str(a).replace(str(s.kok), '<KOK>') for a in args[1:]]}: beklenen {bek!r}\n{_ozet(r)}")
        _sizinti_yok(r)
    c = s.islik / "cikti"
    for args, bek in ((("cikar", "env", s.env, ALAN, "-", c), ESKI_ENV), (("cikar", "dosya", s.dosya, "-", "-", c), ESKI_DOSYA),
                      (("cikar", "url", s.url, "-", "-", c), "eski-parola")):
        r = _yk_sure(s.yardimci, *args, kok=s.kok, sure=SURE)
        _iddia(r is not None and r.returncode == 0 and c.read_text(encoding="utf-8") == bek + "\n", f"{args[:2]}\n{_ozet(r)}")
        c.unlink()


@pytest.mark.skipif(os.geteuid() == 0, reason="root izin bitlerini aşar — 'okuma izni yok' hâli root dışı ölçülür")
def test_C2_IZIN_reddi_ESKI_kovada_kalir_tur_ADI_EKLENMEZ(tmp_path):
    """Okunamayan (izin) NORMAL dosya yeni ret sınıfı DEĞİLDİR: `alan-var tek` → `OKUNAMADI` (tam metin — ön-denetimin
    `OKUNAMADI*` kolu), `tek`siz → `YOK`, `var` → `OKUNAMADI`. Tür adı YALNIZ bağ/FIFO/aygıt/zincir/yarış içindir."""
    s = _OkumaSahnesi(tmp_path)
    s.env.chmod(0o000)
    for args, bek in ((("alan-var", s.env, ALAN, "tek"), "OKUNAMADI"), (("alan-var", s.env, ALAN), "YOK"),
                      (("var", "env", s.env, ALAN), "OKUNAMADI")):
        r = _yk_sure(s.yardimci, *args, kok=s.kok, sure=SURE)
        _iddia(r is not None and r.returncode == 0 and r.stdout.strip() == bek, f"{args[0]}: beklenen {bek!r}\n{_ozet(r)}")
    s.env.chmod(0o640)


# =================================================================================================
# D) N1 — `alan-farki` ADI yalnız ad sözleşmesiyle basar; devam satırı ad DEĞİL; adsız farklar SAYILIR
# =================================================================================================

def _alan_farki(s: _OkumaSahnesi, yedek: str, guncel: str, *haric: str, tur: str = "env") -> subprocess.CompletedProcess:
    m = s.kok / "etc/meridian"
    ad = "json" if tur == "api" else "env"
    (m / f"y.{ad}").write_text(yedek, encoding="utf-8")
    (m / f"g.{ad}").write_text(guncel, encoding="utf-8")
    r = _yk_sure(s.yardimci, "alan-farki", tur, m / f"y.{ad}", m / f"g.{ad}", *haric, kok=s.kok, sure=SURE)
    _iddia(r is not None and r.returncode == 0, _ozet(r))
    return r


#: PEM benzeri çok satırlı değerin GÖVDESİ. Son base64 satırı (`{son}`) YALNIZ büyük harf + rakamdır: satır tabanlı `^AD=` deseni
#: onu KATI sözleşmeyle de ad sanır (`AQAB0123` = `=`).
_PEM_GOVDE = "-----BEGIN PRIVATE KEY-----\nMIIBVwIBADANBgkqhkiG9w0BAQEFAASCAUEwggE9AgEAAkEA\n{son}\n-----END PRIVATE KEY-----"

#: TSK-262 düzeltme turu 1 (inceleme I1, `scratchpad/tsk262-inceleme/n1_sonda.log`): tırnak takibi YALNIZ satır tam `AD="` ile
#: başlıyorsa çalışır; öteki yaygın biçimlerde devam satırı yine `^AD=` desenine düşüyordu. Biçim → (yedek/güncel şablonu, beklenen
#: hüküm). `tirnakli` dışındaki beş biçim İNCELEYİCİNİN biçimleridir (python-dotenv'in geçerli tırnaklı çok satırı ×3 · systemd ters
#: bölü devamı · tırnaksız çok satır); hepsinde base64 satırı TEK tarafta "ad" olur ve YALNIZ sayılır.
_N1_BICIMLER = {
    "tirnakli": ('TLS_ANAHTAR="' + _PEM_GOVDE + '"\n', "FARKLI: TLS_ANAHTAR"),
    "export": ('export TLS_ANAHTAR="' + _PEM_GOVDE + '"\n', "FARKLI: adsız 2 satır"),
    "bosluklu_atama": ('TLS_ANAHTAR = "' + _PEM_GOVDE + '"\n', "FARKLI: adsız 2 satır"),
    "bastaki_bosluk": ('  TLS_ANAHTAR="' + _PEM_GOVDE + '"\n', "FARKLI: adsız 2 satır"),
    "ters_bolu": ("TLS_ANAHTAR=MIIBVwIBADANBgkqhkiG9w0BAQEFAASCAUEw\\\n{son}\n", "FARKLI: adsız 2 satır"),
    "tirnaksiz": ("TLS_ANAHTAR=" + _PEM_GOVDE + "\n", "FARKLI: adsız 2 satır"),
}


@pytest.mark.parametrize("bicim", sorted(_N1_BICIMLER))
def test_D1_COK_SATIRLI_degerin_DEVAM_satiri_HICBIR_BICIMDE_AD_OLARAK_BASILMAZ(tmp_path, bicim):
    """Yedek ile güncel arasında PEM gövdesinin son satırı farklı (`AQAB0123==` → `ZXCV9876==`). İnceleme N1 + düzeltme turu 1 I1:
    satır tabanlı eşleşme bu satırı AD sayıp BASARDI — sır malzemesinin bir parçası. KURAL BİÇİMDEN BAĞIMSIZ: bir ad YALNIZ (a)
    sözleşmeye uyan bir atama olarak İKİ dosyada da var ve değeri farklıysa ya da (b) aranan adlar ∪ sır-adı sonekleri kümesindeyse
    basılır; base64 satırı yalnız TEK tarafta "ad" olur (base64'te `=` yalnız dolgudur) → SAYILIR. `tirnakli` biçimde basılan tek ad
    değerin SAHİBİDİR (`TLS_ANAHTAR`); hiçbir biçimde devam satırının hiçbir parçası çıktıda yok, sonuç "AYNI" değil."""
    s = _OkumaSahnesi(tmp_path)
    sablon, beklenen = _N1_BICIMLER[bicim]
    ortak = f"{ALAN}=x\nHERMES_HOME=/h\n"
    r = _alan_farki(s, ortak + sablon.replace("{son}", "AQAB0123=="), ortak + sablon.replace("{son}", "ZXCV9876=="), ALAN)
    _iddia(r.stdout.strip() == beklenen, f"{bicim}: beklenen {beklenen!r}\n{_ozet(r)}")
    _iddia(not any(p in r.stdout + r.stderr for p in ("AQAB", "ZXCV", "MIIB", "BEGIN")), f"{bicim}: devam satırı çıktıya düştü")


def test_D2_SOZLESME_DISI_ad_BASILMAZ_ADSIZ_sayilir_AYNI_denmez(tmp_path):
    """İnceleme N1'in örneği: TIRNAKSIZ (geçersiz biçim) bir PEM'in son satırı `AbC123xyz==` — gevşek desen (`[A-Za-z_]…`) onu
    ad sayar. YENİ: ad sözleşmesine (`^[A-Z][A-Z0-9_]*$`) uymayan atama/satır YALNIZ sayılır: `FARKLI: adsız 2 satır` (yedekte
    biri, güncelde biri — simetrik fark). Hiçbir parçası basılmaz ve sayı "AYNI" demeyi engeller."""
    s = _OkumaSahnesi(tmp_path)
    ortak = f"{ALAN}=x\nESKI_PEM=-----BEGIN-----\n"
    r = _alan_farki(s, ortak + "AbC123xyz==\n", ortak + "AbC123xyq==\n", ALAN)
    _iddia(r.stdout.strip() == "FARKLI: adsız 2 satır", f"beklenen 'FARKLI: adsız 2 satır'\n{_ozet(r)}")
    _iddia("AbC123" not in r.stdout + r.stderr, "sözleşme dışı satır ad diye basıldı")


def test_D3_AD_ve_ADSIZ_birlikte_yorum_ve_export_satiri_SAYILIR(tmp_path):
    """Sözleşmeye uyan değişmiş ad BASILIR, uymayanlar (yorum · `export X=` · küçük harfli ad) yalnız SAYILIR: `FARKLI: B_ALANI
    + adsız 4 satır`. Değer basılmaz; hariç ad (alt komutun kendi alanı) sayılmaz."""
    s = _OkumaSahnesi(tmp_path)
    r = _alan_farki(s, f"{ALAN}=a\nB_ALANI=1\n# not 1\nexport X=1\nkucuk=1\n",
                    f"{ALAN}=b\nB_ALANI=2\n# not 1\nexport X=2\nkucuk=2\n", ALAN)
    _iddia(r.stdout.strip() == "FARKLI: B_ALANI + adsız 4 satır", f"beklenen 'FARKLI: B_ALANI + adsız 4 satır'\n{_ozet(r)}")
    _iddia("kucuk" not in r.stdout and "export" not in r.stdout, "sözleşme dışı ad basıldı")


def test_D4_MOTOR_DEPOSU_sozlesme_disi_ANAHTAR_basilmaz_SAYILIR(tmp_path):
    """JSON dalı da aynı sözleşme: `NOUS_API_KEY` (hariç) sayılmaz, `TELEGRAM_BOT_TOKEN` basılır, sözleşme dışı anahtar
    (`gizli-parca`) yalnız SAYILIR (`+ adsız 2 anahtar`)."""
    s = _OkumaSahnesi(tmp_path)
    y = {"NOUS_API_KEY": "a", "TELEGRAM_BOT_TOKEN": "1", "gizli-parca": "1"}
    g = {"NOUS_API_KEY": "b", "TELEGRAM_BOT_TOKEN": "2", "gizli-parca": "2"}
    r = _alan_farki(s, json.dumps(y), json.dumps(g), "NOUS_API_KEY", tur="api")
    _iddia(r.stdout.strip() == "FARKLI: TELEGRAM_BOT_TOKEN + adsız 2 anahtar", _ozet(r))
    _iddia("gizli-parca" not in r.stdout, "sözleşme dışı anahtar basıldı")


def test_D5_AD_SOZLESMESI_TEK_KAYNAK_kabuktaki_aranan_adlar_deseniyle_AYNI():
    """Ayrışma çivisi (tek-kaynak yasası — iki dil, tek kural): yardımcının `_AD_SOZLESMESI` deseni kabuktaki `_aranan_adlar`ın
    dosya adı süzgeciyle AYNI dizgedir. Biri gevşerse (ör. `[A-Za-z_]`) bu çivi öter."""
    yardimci = _yardimci_metni()
    m = re.search(r'^_AD_SOZLESMESI = re\.compile\(r"([^"]+)"\)$', yardimci, flags=re.M)
    _iddia(m is not None, "`_AD_SOZLESMESI` tanımı bulunamadı")
    metin = BETIK.read_text(encoding="utf-8")
    aranan = metin[metin.index("_aranan_adlar() {"):]
    aranan = aranan[:aranan.index("\n}\n")]
    _iddia(f"a[n] ~ /{m.group(1)}/" in aranan, f"desen ayrıştı: yardımcı {m.group(1)!r} — `_aranan_adlar` awk süzgecinde yok")


def test_D6_UCTAN_UCA_GERI_AL_KURU_adsiz_farki_SOYLER(tmp_path):
    """Operatörün koşacağı biçim (`--geri-al <yedek> --kuru`): `--kapi` yedeğinden sonra `.env-apisix`e bir yorum satırı
    eklenir (sözleşme dışı, adsız). ESKİ: "başka alan YOK" (satır sayılmıyordu — dosya BÜTÜN döner, yorum da silinir). YENİ: not
    satırı "adsız 1 satır" der; hiçbir şey yazılmaz."""
    kok, ortam, _once, yedek = _kapi_sahnesi(tmp_path)
    apisix = kok / "opt/apisix/.env-apisix"
    apisix.write_text(apisix.read_text(encoding="utf-8") + "# operatör notu\n", encoding="utf-8")
    once = _imzalar(kok)
    r = _kos_sure(ortam, "--geri-al", str(yedek), "--kuru")
    _iddia(r is not None and r.returncode == 0, _ozet(r))
    uyari = _satir_sonrasi(r.stdout, "geri konacak: /opt/apisix/.env-apisix")
    _iddia("BAŞKA alanlar" in uyari and "adsız 1 satır" in uyari, f"uyarı: {_maskeli(uyari)!r}\n{_ozet(r)}")
    _iddia(_imzalar(kok) == once, "kuru koşum YAZDI")
    _sizinti_yok(r)


def _kabuk_sir_adi_mi(adlar: list[str]) -> tuple[list[str], set[str]]:
    """Kabuğun KENDİ `_SIR_ADI_SONEKLERI` + `_sir_adi_mi` tanımını (betikten kesilir — kopya yok) verilen adlarda koşar.
    Döner: (sonek listesi, `_sir_adi_mi` doğru olan adlar)."""
    metin = BETIK.read_text(encoding="utf-8")
    deger = re.search(r'^_SIR_ADI_SONEKLERI="([^"]+)"$', metin, flags=re.M)
    _iddia(deger is not None, "`_SIR_ADI_SONEKLERI` tanımı bulunamadı")
    fonk = metin[metin.index("_sir_adi_mi() {"):]
    fonk = fonk[:fonk.index("\n}\n") + 3]
    kod = f'_SIR_ADI_SONEKLERI="{deger.group(1)}"\n{fonk}\nfor a in "$@"; do if _sir_adi_mi "$a"; then echo "$a"; fi; done\n'
    r = subprocess.run(["bash", "-c", kod, "_", *adlar], capture_output=True, text=True)
    _iddia(r.returncode == 0, r.stderr[-1000:])
    return deger.group(1).split(), set(r.stdout.split())


def test_D7_TEK_TARAFLI_ad_YALNIZ_sir_adi_sonekiyle_BASILIR_kabukla_AYNI_kural(tmp_path):
    """I1 kuralının (b) kolu, sonek yarısı — tek kaynaktan: yardımcı sonek listesini kabuktan alır (`--sonek $_SIR_ADI_SONEKLERI`)
    ve `_sir_adi_mi` ile AYNI anlamı uygular (son-ek eşleşmesi). Ayrışma çivisi: yalnız güncelde bulunan sekiz addan yardımcının
    BASTIKLARI = kabuğun `_sir_adi_mi`sinin DOĞRU dedikleri; kalanlar yalnız SAYILIR. Pozitif kontrol: kabuk dört adı seçer."""
    s = _OkumaSahnesi(tmp_path)
    adlar = ["YENI_TOKEN", "YENI_API_KEY", "YENI_SECRET", "YENI_PASSWORD", "YENI_TOKENS", "TOKEN_YENI", "YENI_KEY", "APIKEY_X"]
    sonekler, kabuk = _kabuk_sir_adi_mi(adlar)
    _iddia(kabuk == {"YENI_TOKEN", "YENI_API_KEY", "YENI_SECRET", "YENI_PASSWORD"}, f"pozitif kontrol: kabuk {sorted(kabuk)}")
    r = _alan_farki(s, f"{ALAN}=x\n", f"{ALAN}=x\n" + "".join(f"{a}=1\n" for a in adlar), ALAN, "--sonek", *sonekler)
    _iddia(r.stdout.startswith("FARKLI: "), _ozet(r))
    govde = r.stdout.strip()[len("FARKLI: "):]
    basilan = set(govde.split(" + ")[0].split()) if not govde.startswith("adsız") else set()
    _iddia(basilan == kabuk and govde.endswith("+ adsız 4 satır"), f"yardımcı {sorted(basilan)} ≠ kabuk {sorted(kabuk)}\n{_ozet(r)}")


def test_D8_UCTAN_UCA_GERI_AL_KURU_aranan_ad_BASILIR_sirsiz_tek_tarafli_ad_SAYILIR(tmp_path):
    """I1 kuralının (b) kolu, aranan adlar yarısı — operatörün biçimi (`--geri-al <yedek> --kuru`): `--kapi` yedeğinden sonra
    `.env-apisix`e iki satır eklenir: `HINDSIGHT_CP_ACCESS_KEY` (`_aranan_adlar`da — tablonun sır kimliği; sır-adı sözlüğüne UYMAZ)
    ve `KENDI_AYARI` (ne aranan ne sır-adı). Not satırı ilkini ADIYLA basar (kabuk `--basilir $(_aranan_adlar)` geçer), ikincisini
    yalnız SAYAR (bedel: yedekten sonra eklenen sırsız ad adıyla söylenmez). Hiçbir şey yazılmaz, değer basılmaz."""
    kok, ortam, _once, yedek = _kapi_sahnesi(tmp_path)
    apisix = kok / "opt/apisix/.env-apisix"
    apisix.write_text(apisix.read_text(encoding="utf-8") + "HINDSIGHT_CP_ACCESS_KEY=x\nKENDI_AYARI=1\n", encoding="utf-8")
    once = _imzalar(kok)
    r = _kos_sure(ortam, "--geri-al", str(yedek), "--kuru")
    _iddia(r is not None and r.returncode == 0, _ozet(r))
    uyari = _satir_sonrasi(r.stdout, "geri konacak: /opt/apisix/.env-apisix")
    _iddia("ESKİYE döner: HINDSIGHT_CP_ACCESS_KEY + adsız 1 satır" in uyari and "KENDI_AYARI" not in uyari,
           f"uyarı: {_maskeli(uyari)!r}\n{_ozet(r)}")
    _iddia(_imzalar(kok) == once, "kuru koşum YAZDI")
    _sizinti_yok(r)


# =================================================================================================
# E) N2 — yarım yedek `.yarim` (girdi DEĞİL) · ön yedeğin KOKEN dosyası · yedek listesinde üç sınıf
# =================================================================================================

def _gecerli_adli_yeni(kok: pathlib.Path, haric: pathlib.Path | None = None) -> list[pathlib.Path]:
    return [y for y in _yedekler(kok) if y != haric and re.fullmatch(r"sir-yedek-\d{8}T\d{6}Z-[a-z][a-z0-9-]*", y.name)]


def test_E1_GERI_AL_on_yedegi_YARIDA_kalirsa_YARIM_adina_tasinir_GIRDI_olarak_REDDEDILIR(tmp_path):
    """F4a sahnesi (`.env-apisix` bir kurbana bağ): `--geri-al`ın ön yedeği kapi_apikey'i kopyalar, `.env-apisix`te adlı retle
    durur (çıkış 1). ESKİ: yarım dizin GEÇERLİ adla kalıyordu (`sir-yedek-<ts>-kapi`) — sonradan onunla `--geri-al` eksik dosyayı
    "o koşumda yoktu" diye yanlış adlandırıp yarım geri alma yapardı (yeniden inceleme N2). YENİ: geçerli adlı yeni dizin YOK,
    tek bir `<ad>.yarim` var (KOKEN'i taşır — kopyalardan önce yazıldı), stderr bunu ADIYLA söyler; o dizinle `--geri-al` çıkış 1
    + "YARIM" ile hiçbir şey yazmadan reddeder; envanterin yedek listesi onu YARIM diye adlar."""
    kok, ortam, _once, yedek = _kapi_sahnesi(tmp_path)
    apisix = kok / "opt/apisix/.env-apisix"
    kurban = tmp_path / "disari_kurban"
    kurban.write_text(f"KURBAN_SATIRI={IZ}\n", encoding="utf-8")
    apisix.unlink()
    apisix.symlink_to(kurban)
    r = _kos_sure(ortam, "--geri-al", str(yedek))
    _iddia(r is not None and r.returncode == 1 and "yedek ALINAMADI: /opt/apisix/.env-apisix" in r.stderr, _ozet(r))
    _iddia(not _gecerli_adli_yeni(kok, yedek), f"yarım ön yedek GEÇERLİ adla kaldı: {_gecerli_adli_yeni(kok, yedek)}")
    yarim = [y for y in _yedekler(kok) if y.name.endswith(".yarim")]
    _iddia(len(yarim) == 1 and re.fullmatch(r"sir-yedek-\d{8}T\d{6}Z-kapi\.yarim", yarim[0].name), f"yarım dizin: {yarim}")
    _iddia(f"YARIM YEDEK: {yarim[0]}" in r.stderr, _ozet(r))
    _iddia((yarim[0] / "KOKEN").is_file(), "yarım ön yedek kökenini taşımıyor (KOKEN kopyalardan ÖNCE yazılmalı)")
    once = _imzalar(kok)
    rr = _kos_sure(ortam, "--geri-al", str(yarim[0]))
    _iddia(rr is not None and rr.returncode == 1 and "YARIM" in rr.stderr, _ozet(rr))
    _iddia(_imzalar(kok) == once, "YARIM yedekle --geri-al bir şey YAZDI")
    re_ = _kos_sure(ortam, "--envanter")
    _iddia(re_ is not None and f"{yarim[0]}  (YARIM" in re_.stdout, _ozet(re_))
    for x in (r, rr, re_):
        _sizinti_yok(x)


def test_E2_ROTASYON_yedegi_YARIDA_kalirsa_da_YARIM_adina_tasinir(tmp_path):
    """Sınıf bir örnekle kapanmaz: aynı gövde (`_yedek_al`) rotasyon yedeğidir. v611 B1 sahnesi — yedek dizini açılırken
    (`install -d … sir-yedek-…`) karne `.env`i bir kök dosyasına bağ olur: `--tenant` "yedek ALINAMADI" ile durur. Geçerli
    adlı yedek dizini KALMAZ, `…-tenant.yarim` vardır (rotasyon yedeğinde KOKEN YOKTUR)."""
    kok, ortam = _sahte_ortam(tmp_path)
    kurban = kok / "etc/meridian/gizli"
    kurban.write_text(f"GIZLI={IZ}\n", encoding="utf-8")
    karne = kok / "home/ubuntu/.hermes-botlar/profiles/karne/.env"
    isaret = _sudo_kancasi(tmp_path, ortam, 'a[:1] == ["install"] and "sir-yedek-" in a[-1]',
                           f"os.unlink({str(karne)!r})\nos.symlink({str(kurban)!r}, {str(karne)!r})")
    r = _kos_sure(ortam, "--tenant")
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    _iddia(r is not None and r.returncode == 1 and "yedek ALINAMADI" in r.stderr, _ozet(r))
    _iddia(not _gecerli_adli_yeni(kok), f"yarım rotasyon yedeği GEÇERLİ adla kaldı: {_gecerli_adli_yeni(kok)}")
    yarim = [y for y in _yedekler(kok) if y.name.endswith(".yarim")]
    _iddia(len(yarim) == 1 and yarim[0].name.endswith("-tenant.yarim") and not (yarim[0] / "KOKEN").exists(),
           f"yarım dizin: {yarim}")
    _sizinti_yok(r)


def test_E3_ON_YEDEK_KOKEN_tasir_DEGER_tasimaz_sisteme_GERI_KONMAZ_listede_AYRILIR(tmp_path):
    """Başarılı `--geri-al`: ön yedek `KOKEN` taşır — TAM dört satır (`tur: on-yedek` · `kaynak: --geri-al <girdi>` · `alt: kapi`
    · `damga: <dizin adındaki UTC damga>`), 0600, hiçbir sır değeri yok. Girdi (rotasyon yedeği) KOKEN taşımaz. KOKEN tablo
    yolu değildir: sonraki `--geri-al` onu sisteme KOYMAZ. `--envanter`in yedek listesi: rotasyon yedeği ESKİ biçimde (yalnız
    yol), ön yedek "ÖN YEDEK" ile; `--geri-al <ön yedek> --kuru` girdinin ön yedek olduğunu söyler."""
    kok, ortam, _once, yedek = _kapi_sahnesi(tmp_path)
    r = _kos_sure(ortam, "--geri-al", str(yedek))
    _iddia(r is not None and r.returncode == 0, _ozet(r))
    on = _gecerli_adli_yeni(kok, yedek)
    _iddia(len(on) == 1, f"ön yedek sayısı {len(on)}")
    koken = on[0] / "KOKEN"
    damga = re.fullmatch(r"sir-yedek-(\d{8}T\d{6}Z)-kapi", on[0].name).group(1)
    _iddia(koken.is_file() and (koken.stat().st_mode & 0o777) == 0o600, "KOKEN yok ya da 0600 değil")
    _iddia(koken.read_text(encoding="utf-8") == f"tur: on-yedek\nkaynak: --geri-al {yedek}\nalt: kapi\ndamga: {damga}\n",
           "KOKEN içeriği beklenen dört satır değil")
    _iddia(not any(d.encode() in koken.read_bytes() for d in _DEGERLER), "KOKEN bir sır değeri taşıyor")
    _iddia(not (yedek / "KOKEN").exists(), "rotasyon yedeği KOKEN taşıyor")
    geri_geri = _eskit(on[0], "20240102T000000Z")
    rk = _kos_sure(ortam, "--geri-al", str(geri_geri), "--kuru")
    _iddia(rk is not None and rk.returncode == 0 and "köken: girdi bir ÖN YEDEK" in rk.stdout, _ozet(rk))
    rr = _kos_sure(ortam, "--geri-al", str(geri_geri))
    _iddia(rr is not None and rr.returncode == 0, _ozet(rr))
    _iddia(not [p for p in kok.rglob("KOKEN") if p.relative_to(kok).parts[0] != "root"], "KOKEN sisteme GERİ KONDU")
    re_ = _kos_sure(ortam, "--envanter")
    _iddia(re_ is not None and re_.returncode == 0, _ozet(re_))
    satirlar = re_.stdout.splitlines()
    _iddia(str(yedek) in satirlar, "rotasyon yedeğinin satırı ESKİ biçimde (yalnız yol) değil")
    _iddia(any(s.startswith(f"{geri_geri}  (ÖN YEDEK") for s in satirlar), "ön yedek listede AYRILMIYOR")
    for x in (r, rk, rr, re_):
        _sizinti_yok(x)


def test_E4_GERI_AL_girdi_kalibi_TABLODAKI_her_alt_komutu_kabul_eder():
    """Girdi kalıbı daraldı (alt `[a-z][a-z0-9-]*` — `.yarim` reddedilsin): tablodaki HER alt komut kalıba uymalı, yoksa o alt
    komutun geçerli yedeği `--geri-al`a girdi olamaz. Ayrışma çivisi: tabloya kalıp dışı bir alt ad girerse öter."""
    r = subprocess.run(["bash", str(BETIK), "--kopyalar"], capture_output=True, text=True)
    _iddia(r.returncode == 0, r.stderr[-2000:])
    altlar = {s.split()[0] for s in r.stdout.splitlines() if s.strip()}
    _iddia(len(altlar) >= 8, f"tablo okunamadı: {altlar}")
    metin = BETIK.read_text(encoding="utf-8")
    _iddia(r"Z-\([a-z][a-z0-9-]*\)$/\1/p" in metin, "`geri_al` girdi kalıbı beklenen biçimde değil")
    disari = sorted(a for a in altlar if not re.fullmatch(r"[a-z][a-z0-9-]*", a))
    _iddia(not disari, f"girdi kalıbına uymayan alt komut(lar): {disari}")


# =================================================================================================
# F) UÇTAN UCA — `--envanter` FIFO/bağda ASKIDA KALMAZ, okunamayanı ADLAR, "YOK" uydurmaz
# =================================================================================================

@pytest.mark.parametrize("hal", ["kopya_fifo", "referans_fifo"])
def test_F1_ENVANTER_tablo_kopyasi_ya_da_referans_FIFO_ASKIDA_KALMAZ(tmp_path, hal):
    """Operatörün biçimi (`--envanter`). (kopya_fifo) GLOBAL hermes `.env` (OpenRouter kopyası, ubuntu dizini) FIFO; (referans_fifo)
    OpenRouter REFERANSI (`HINDSIGHT_API_LLM_API_KEY`) FIFO. ESKİ: envanter `open()`da SÜRESİZ asılır. YENİ: çıkış 0, ilgili satır
    `OKUNAMADI (FIFO)` (referans tarafı kopya satırlarında `REFERANS OKUNAMADI (FIFO)`), değer basılmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    yol = kok / ("home/ubuntu/.hermes/.env" if hal == "kopya_fifo" else "etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY")
    yol.unlink()
    os.mkfifo(yol, 0o600)
    r = _kos_sure(ortam, "--envanter")
    _iddia(r is not None, "--envanter FIFO'da ASKIDA KALDI")
    _iddia(r.returncode == 0, _ozet(r))
    if hal == "kopya_fifo":
        _iddia(any("/home/ubuntu/.hermes/.env [OPENROUTER_API_KEY] → OKUNAMADI (FIFO)" in s for s in r.stdout.splitlines()),
               _ozet(r))
    else:
        _iddia("HINDSIGHT_API_LLM_API_KEY → OKUNAMADI (FIFO) (referans kopya)" in r.stdout
               and "→ REFERANS OKUNAMADI (FIFO)" in r.stdout, _ozet(r))
    _sizinti_yok(r)


@pytest.mark.parametrize("hal", ["tarama_bag", "tarama_fifo", "depo_bag"])
def test_F2_ENVANTER_beyan_disi_taramasi_okunamayani_TARANAMADI_der_YOK_uydurmaz(tmp_path, hal):
    """(tarama_bag) taranan `/opt/meridian/.env` bir kurbana bağ — ESKİ: `test -f` bağı izler, root kurbanı okur ve onun adını
    "BEYAN DIŞI KOPYA" diye basardı. (tarama_fifo) aynı dosya FIFO — ESKİ: `test -f` "yok" sayıp SESSİZCE atlardı. (depo_bag) motor
    deposu `secrets.json` bağ. YENİ: dosya BİR kez "TARANAMADI … OKUNAMADI (<tür>)" diye adlanır, tarama sonu "YOK" DEMEZ (EKSİK
    der), kurbanın adı/değeri basılmaz, askı yok."""
    kok, ortam = _sahte_ortam(tmp_path)
    kurban = kok / "etc/meridian/gizli_iz"
    if hal == "depo_bag":
        yol = kok / "opt/meridian/state/secrets.json"
        kurban.write_text(json.dumps({"IZ_DASH_TOKEN": IZ}) + "\n", encoding="utf-8")
    else:
        yol = kok / "opt/meridian/.env"
        kurban.write_text(f"IZ_DASH_TOKEN={IZ}\n", encoding="utf-8")
    yol.unlink()
    if hal == "tarama_fifo":
        os.mkfifo(yol, 0o600)
        tur = "FIFO"
    else:
        yol.symlink_to(kurban)
        tur = "SEMBOLİK BAĞ"
    r = _kos_sure(ortam, "--envanter")
    _iddia(r is not None and r.returncode == 0, _ozet(r))
    rel = "/" + str(yol.relative_to(kok))
    _iddia(f"!! TARANAMADI: {rel} — OKUNAMADI ({tur})" in r.stdout, _ozet(r))
    _iddia("IZ_DASH_TOKEN" not in r.stdout + r.stderr, "bağın HEDEFİNDEKİ ad basıldı (bağ izlendi)")
    if hal != "depo_bag":
        _iddia("beyan dışı kopya YOK" not in r.stdout and "taraması EKSİK: 1 dosya TARANAMADI" in r.stdout, _ozet(r))
    _sizinti_yok(r)


@pytest.mark.parametrize("hal", ["kopya_fifo", "referans_fifo"])
def test_F3_ESITLE_kaniti_OKUNAMAYAN_satiri_ESIT_saymaz_OLCULEMEDI_cikis_2(tmp_path, hal):
    """TSK-262 düzeltme turu 1 (inceleme M3): `--openrouter --esitle`, global hermes `.env` AYRI (TSK-181 sahnesi). (kopya_fifo)
    ikinci geçişte referans çıkarılırken AYRI kopya FIFO'ya çevrilir → ikinci geçiş onu `OKUNAMADI (FIFO)` görür ve YAZMAZ;
    (referans_fifo) yazım anında REFERANS FIFO'ya çevrilir → kanıtta kopyalar `REFERANS OKUNAMADI (FIFO)`. ESKİ kanıt yalnız
    `→ AYRI` arıyordu: "kopyaları EŞİT" + çıkış 0 — YANLIŞ BAŞARI. YENİ: referans olmayan her satır `→ EŞİT` olmalı (motor API /
    ALTER ROLE satırları beyanlı kanaldır, hariç); değilse ÖLÇÜLEMEDİ, çıkış 2 (aracın ölçülemedi sınıfı). Değer basılmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    _global_ayir(kok)
    if hal == "kopya_fifo":
        hedef, kosul = kok / GLOBAL_HERMES, '"cikar" in a and a[-1].endswith("/ref_OPENROUTER_API_KEY")'
        satir = "/home/ubuntu/.hermes/.env [OPENROUTER_API_KEY] → OKUNAMADI (FIFO)"
    else:
        hedef, kosul = kok / "etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY", '"yaz-env" in a'
        satir = "→ REFERANS OKUNAMADI (FIFO)"
    isaret = _sudo_kancasi(tmp_path, ortam, kosul, f"os.unlink({str(hedef)!r})\nos.mkfifo({str(hedef)!r}, 0o600)")
    r = _kos_sure(ortam, "--openrouter", "--esitle")
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    _iddia(r is not None and satir in r.stdout, f"kanıt satırı yok: {satir!r}\n{_ozet(r)}")
    _iddia(r.returncode == 2 and "ÖLÇÜLEMEDİ" in r.stderr and "kopyaları EŞİT" not in r.stdout,
           f"okunamayan kopya EŞİT sayıldı (yanlış başarı)\n{_ozet(r)}")
    _sizinti_yok(r)


# =================================================================================================
# K) K1 — DOSYA İÇİ kısmi önlem: çalışma dizini `/` + her python `-I` (A0 root sahipli kurulum yeri ayrı kalem: TSK-265)
# =================================================================================================
# İnceleme K1(b) (`scratchpad/tsk262-inceleme/cwd_sonda/`): `python3 -c` sys.path'in başına ÇALIŞMA DİZİNİNİ koyar; RUNBOOK biçimi
# `cd /opt/meridian && sudo ./deploy/oracle-a1/sir_rotasyon.sh …` ile ubuntu'nun yazabildiği dizindeki bir `yaml.py`/`ast.py` root
# olarak koşar. İki katman: betik başta kendi dizinini MUTLAK yola çözüp `cd /` yapar; her python çağrısı `-I` (yalıtılmış kip —
# ne çalışma dizini ne betik dizini ne `PYTHON*` ortamı sys.path'e girer). Katmanlar ayrı ayrı ısırılır: K1a `PYTHONPATH` yoluyla
# `-I`yı (çalışma dizini yolunu `cd /` zaten kapatır), K1b çocuk süreçlerin çalışma dizinini (`cd /`).

_SAHTE_MODUL = "import sys\nwith open({isaret!r}, 'a') as _f:\n    _f.write(repr(sys.argv) + '\\n')\n"


def _sahte_moduller(dizin: pathlib.Path, isaret: pathlib.Path) -> None:
    """İÇE AKTARILIRSA işaret dosyasına sürecin argv'sini yazan sahte modüller: `yaml` + `ast` (kabuk parçacıkları — envanter /
    üretici okuması) ve `urllib` paketi (gömülü yardımcı `urllib.parse` ister). Çivi şimleri (`json` · `os` · `re` · `shutil` ·
    `sys`) bunların hiçbirini içe aktarmaz — işaret YALNIZ betiğin kendi yorumlayıcılarından gelebilir."""
    dizin.mkdir(parents=True, exist_ok=True)
    govde = _SAHTE_MODUL.format(isaret=str(isaret))
    (dizin / "yaml.py").write_text(govde, encoding="utf-8")
    (dizin / "ast.py").write_text(govde, encoding="utf-8")
    (dizin / "urllib").mkdir(exist_ok=True)
    (dizin / "urllib/__init__.py").write_text(govde, encoding="utf-8")


def _kasa_ortami(tmp_path: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """`_sahte_ortam` + PyYAML'lı yorumlayıcı (`PYTHON_BIN` — çivinin kendi `.venv`i): kasaya bağlı alt komutun Agent hedefi
    uyarısı depo girdilerinden (`sir_envanteri.yaml` · `vault_politika_uret.py`) GERÇEKTEN okunsun."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["PYTHON_BIN"] = sys.executable
    return kok, ortam


#: `--kapi --kuru` çıktısında depo girdilerinin OKUNDUĞUNUN kanıtı: kasa yolu `sir_envanteri.yaml`den (yaml parçacığı), aralık
#: `vault_politika_uret.py`den (ast parçacığı) gelir — girdi bulunamazsa satır yerine "UYARI ÖLÇÜLEMEDİ" basılır.
_DEPO_GIRDISI_KANITI = ("kasa yolu: secret/meridian/kapi_apikey (vault_kv.kapi_apikey)", "aralık: 1m (ops/vault_politika_uret.py")


def test_K1a_CALISMA_DIZINI_ve_PYTHONPATH_teki_sahte_yaml_ast_urllib_ICE_AKTARILMAZ(tmp_path):
    """Operatörün biçimi — GERÇEK `--kapi` (Agent hedefi uyarısı yaml/ast parçacıklarını; ön-denetim, yedek, yazım ve kanıt gömülü
    yardımcıyı `sudo python3` ile koşar; `--kuru` hiç `sudo` çağırmaz, ölçüldü) — ÇALIŞMA DİZİNİ sahte modüllerle dolu bir dizin ve
    `PYTHONPATH` o dizin. ESKİ: `python3 -c` çalışma dizinini sys.path'e koyar → sahte `yaml`/`ast` root olarak koşar (işaret
    yazılır). YENİ: işaret YOK, depo girdileri yine okunur (kanıt satırları), çıkış 0. `PYTHONPATH` ayağı `-I`yı tek başına ısırır —
    parçacıklarda (`yaml`/`ast`) ve gömülü yardımcıda (`urllib`) ayrı ayrı (`cd /` onu kapatmaz; üretimde `sudo` ortamı sıfırlar —
    çivide yalıtımın ölçü aletidir)."""
    kok, ortam = _kasa_ortami(tmp_path)
    sahte, isaret = tmp_path / "sahte_moduller", tmp_path / "sahte_ice_aktarildi"
    _sahte_moduller(sahte, isaret)
    ortam["PYTHONPATH"] = str(sahte)
    r = _kos_sure(ortam, "--kapi", cwd=sahte)
    _iddia(not isaret.exists(), "sahte modül İÇE AKTARILDI: " + (isaret.read_text(encoding="utf-8")[-800:] if isaret.exists() else ""))
    _iddia(any(" kopyala " in x for x in (kok / ".sahte/argv.log").read_text(encoding="utf-8").splitlines()),
           "gömülü yardımcı `sudo` ile HİÇ koşmadı — `py` ayağı kör (pozitif kontrol)")
    _iddia(r is not None and r.returncode == 0 and all(k in r.stdout for k in _DEPO_GIRDISI_KANITI), _ozet(r))
    _sizinti_yok(r)


def test_K1b_BETIK_cocuk_surecleri_KOK_DIZINDE_kosturur(tmp_path):
    """`cd /` katmanı: betik nereden çağrılırsa çağrılsın çocuk süreçlerinin (sudo → yardımcı · yaml/ast parçacıkları) çalışma dizini
    `/`dir — ubuntu'nun yazabildiği çağrı dizini (RUNBOOK: `cd /opt/meridian && sudo ./deploy/…`) hiçbir göreli aramaya girmez.
    Ölçüm: GERÇEK `--kapi`nin ilk `sudo` çağrısında şim kancası çalışma dizinini kaydeder."""
    kok, ortam = _kasa_ortami(tmp_path)
    cagri = tmp_path / "cagri_dizini"
    cagri.mkdir()
    kayit = tmp_path / "cocuk_cwd"
    isaret = _sudo_kancasi(tmp_path, ortam, "True", f"open({str(kayit)!r}, 'w').write(os.getcwd())")
    r = _kos_sure(ortam, "--kapi", cwd=cagri)
    _iddia(isaret.exists() and kayit.exists(), f"kanca ATEŞLENMEDİ (pozitif kontrol)\n{_ozet(r)}")
    _iddia(os.path.realpath(kayit.read_text(encoding="utf-8")) == "/", f"çocuk sürecin çalışma dizini: {kayit.read_text()!r}")
    _iddia(r is not None and r.returncode == 0, _ozet(r))


def test_K1c_GORELI_cagrida_depo_girdileri_BULUNUR_cikti_MUTLAK_cagriyla_AYNI(tmp_path):
    """Betik dizini `cd /`dan ÖNCE MUTLAK yola çözülür: göreli çağrı (`bash deploy/oracle-a1/sir_rotasyon.sh`, çalışma dizini depo
    kökü — RUNBOOK'un `./deploy/…` biçimi) depo girdilerini yine bulur; çıktı mutlak çağrınınkiyle AYNIDIR (betik yolu metni
    soyulur). Çözüm `cd /`dan SONRA ya da göreli kalsaydı girdiler `/` altında aranır, kanıt satırları "UYARI ÖLÇÜLEMEDİ"ye döner."""
    kok, ortam = _kasa_ortami(tmp_path)
    goreli = str(BETIK.relative_to(KOK_DEPO))
    rg = _kos_sure(ortam, "--kapi", "--kuru", cwd=KOK_DEPO, betik=goreli)
    rm = _kos_sure(ortam, "--kapi", "--kuru")
    _iddia(rg is not None and rg.returncode == 0 and all(k in rg.stdout for k in _DEPO_GIRDISI_KANITI), _ozet(rg))
    _iddia(rm is not None and rm.returncode == 0, _ozet(rm))
    _iddia(rg.stdout.replace(goreli, "<BETIK>") == rm.stdout.replace(str(BETIK), "<BETIK>"),
           "göreli çağrının çıktısı mutlak çağrınınkinden AYRIŞTI")


def test_K1d_STATIK_betikte_YALITILMAMIS_python_cagrisi_KALMADI():
    """Kabuk tarafının (gömülü yardımcı metni ve yorumlar hariç) BÜTÜN yorumlayıcı çağrıları — `"$PYTHON_BIN" …` ve `python3 …` —
    `-I` ile başlar; `py()` (gömülü yardımcı) dahil. Sayı PINLENİR (ölçüldü 2026-10-02: 7 — saat okuması · dört depo girdisi
    parçacığı · kasa sürümü · `py`): tarama kör kalırsa ya da yeni bir çağrı eklenirse öter. Betiğin başında `cd /` ve mutlak betik
    dizini, depo girdileri o dizinden türer."""
    metin = BETIK.read_text(encoding="utf-8")
    bas = metin.index("<<'PY_SON'\n")
    kabuk = metin[:bas] + metin[metin.index("\nPY_SON\n", bas):]
    satirlar = [x for x in kabuk.splitlines() if x.strip() and not x.lstrip().startswith("#")]
    cagrilar = [(x.strip(), m.group(1)) for x in satirlar
                for m in re.finditer(r'(?:"\$PYTHON_BIN"|\bpython3)[ \t]+(\S+)', x)]
    _iddia(len(cagrilar) == 7, f"yorumlayıcı çağrısı sayısı {len(cagrilar)} (ölçülen 7): " + "\n".join(c for c, _ in cagrilar))
    yalitilmamis = [c for c, ilk in cagrilar if ilk != "-I"]
    _iddia(not yalitilmamis, "-I'sız yorumlayıcı çağrısı:\n" + "\n".join(yalitilmamis))
    on = metin[metin.index("set -euo pipefail"):metin.index('KOK="${SIR_ROT_KOK:-}"')]
    _iddia(re.search(r'^BETIK_DIZINI="\$\(cd "\$\(dirname "\$0"\)" && pwd -P\)"', on, flags=re.M) is not None
           and re.search(r"^cd /$", on, flags=re.M) is not None, "betik başında mutlak dizin çözümü + `cd /` yok")
    for ad in ("VAULT_ENVANTER", "VAULT_POLITIKA_URETICI"):
        _iddia(re.search(rf'^{ad}="\$\{{{ad}:-\$BETIK_DIZINI/', metin, flags=re.M) is not None, f"{ad} betik dizininden türemiyor")


# =================================================================================================
# G) STATİK — çıplak `open()` yok; ölçülen istisnalar DEPO İÇİ sabit girdiler; okuma gövdesi TEK
# =================================================================================================

def test_G1_STATIK_yardimcida_CIPLAK_open_YOK_okuma_TEK_govdeden():
    """Yardımcının AST'sinde `open(` (yerleşik) çağrısı YOK — her dosya okuması `_oku`dan (`_hedef_ac` + `_tanitictan_oku`
    okuma kipi) geçer; `_tanitictan_oku` açılış bayraklarını (`O_NOFOLLOW|O_NONBLOCK`) ve tür denetimini (`S_ISREG`) taşır.
    Ayrı bir okuma çekirdeği (`_guvenli_metin`) KALMADI."""
    yardimci = _yardimci_metni()
    agac = ast.parse(yardimci.split("\n", 1)[1])
    cagrilar = [n.lineno for n in ast.walk(agac)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open"]
    _iddia(not cagrilar, f"yardımcıda çıplak open() çağrısı: satır {cagrilar}")
    oku = _fonksiyon(yardimci, "_oku")
    _iddia("_hedef_ac(" in oku and "_tanitictan_oku(" in oku and "os.lstat(" in oku, "`_oku` ortak çekirdekten geçmiyor")
    tanitic = _fonksiyon(yardimci, "_tanitictan_oku")
    _iddia("O_NOFOLLOW | os.O_NONBLOCK" in tanitic and "S_ISREG" in tanitic, "`_tanitictan_oku` bayrak/tür denetimi yok")
    _iddia("def _guvenli_metin(" not in yardimci and yardimci.count("def _oku(") == 1, "ikinci okuma çekirdeği var")


def test_G2_STATIK_yardimci_DISI_open_YALNIZ_depo_ici_SABIT_girdiler():
    """Ölçülen istisnalar (brief): kabuktaki AYRI python parçacıkları `yaml.safe_load(open(sys.argv[1]))` /
    `ast.parse(open(sys.argv[1]))` — girdileri `$VAULT_ENVANTER` (`deploy/sir_envanteri.yaml`) ve `$VAULT_POLITIKA_URETICI`
    (`ops/vault_politika_uret.py`): betiğin KENDİ deposundaki dosyalar, yani betiği koşturan güvenle aynı güven sınıfı (onları
    değiştirebilen betiğin kendisini de değiştirir — `_capa`nın "yardımcının kendi dizini" gerekçesi). Kümeyi PINLER: yeni bir
    yardımcı-dışı `open(` ya da başka bir girdiye bağlanan parçacık bu çiviyi öttürür."""
    metin = BETIK.read_text(encoding="utf-8")
    bas = metin.index("<<'PY_SON'\n")
    son = metin.index("\nPY_SON\n", bas)
    disari = metin[:bas] + metin[son:]
    satirlar = disari.splitlines()
    bulunan = [i for i, s in enumerate(satirlar) if re.search(r"(?<![\w.])open\(", s) and not s.lstrip().startswith("#")]
    _iddia(len(bulunan) == 4, f"yardımcı dışı open() sayısı {len(bulunan)} (ölçülen 4)")
    for i in bulunan:
        _iddia("open(sys.argv[1], encoding=\"utf-8\")" in satirlar[i], f"beklenmeyen biçim: {satirlar[i].strip()}")
        kapanis = next(s for s in satirlar[i + 1:] if s.startswith("' "))
        _iddia(kapanis.startswith(("' \"$VAULT_ENVANTER\"", "' \"$VAULT_POLITIKA_URETICI\"")),
               f"parçacığın girdisi depo içi sabit değil: {kapanis.strip()}")
    for ad in ("VAULT_ENVANTER", "VAULT_POLITIKA_URETICI"):
        tanim = re.search(rf'^{ad}="\$\{{{ad}:-\$BETIK_DIZINI/[^}}]+\}}"$', metin, flags=re.M)   # K1: mutlak betik dizini
        _iddia(tanim is not None, f"{ad} varsayılanı betiğin deposuna bağlı değil")

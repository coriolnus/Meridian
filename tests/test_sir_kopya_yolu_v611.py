"""test_sir_kopya_yolu_v611.py — TSK-261: sır rotasyon aracının KOPYA-tabanlı yollarında sembolik bağ sınıfı (CWE-59/367)
+ TSK-260 incelemesinin üç Minörü (M1 FIFO · M2 dizin yeniden adlandırma · M3 ön-denetim kapsamı).

NUMARA: `ls tests | grep v611` boş — bu worktree, ana checkout ve bütün `.claude/worktrees/*/tests` (ölçüldü 2026-10-01; en
yüksek v610, `edg103-sayim` worktree'sinde).

SINIF. TSK-260 yardımcının YAZIM yolunu fd-tabanlı tek gövdeye taşıdı (`_atomik_yaz` · `_hedef_ac` · `_gecici_yaz` ·
`_gecici_dogrula` · `_yazim_kusurlari`). Aracın KOPYA yolları kabuktaydı ve root olarak bağ İZLİYORDU:
  · `_negatif_geri_al` — `sudo cp -p <yedek> "$hedef.yeni" && sudo mv -f …`: `.yeni` ÖNGÖRÜLEBİLİR bir addır; hedef dizinin
    sahibi (ubuntu — hermes profilleri, `/opt/hindsight`, `/opt/meridian/state`) onu önceden bir bağ olarak kurarsa root `cp`
    bağı izler, seçilen dosyayı yedeğin içeriğiyle EZER ve `-p` ile sahibini ubuntu'ya verir; `mv -f` bağı hedefin yerine
    koyar. HER `--openrouter` koşumunun OLAĞAN yoludur (negatif kontrol geri alması — arıza yolu değil).
  · `_yedek_al` / `_negatif_kontrol` — `sudo cp -p <kaynak> <yedek>`: KAYNAK bağını izler (root-yalnız dizine kopya; zincirde
    geri alma ile ubuntu dizinine geri döner).
  · basılan reçeteler — `sudo cp -p <yedek>/<yol> /<yol>`: operatör koşar, hedef bağını izler.

YENİ SÖZLEŞME — yardımcının `kopyala <kaynak> <hedef>` işlemi (bağ İZLEMEYEN `cp -p`): kaynak `_hedef_ac` (koru) +
`_tanitictan_oku` (ikili, `O_NOFOLLOW|O_NONBLOCK` + fstat normal dosya + inode) ile, hedef `_atomik_yaz` ile (öngörülebilir
ad YOK — geçici `.sir-rot-<rastgele>` `O_EXCL|O_NOFOLLOW`), mod/sahip KAYNAĞIN (`-p`). Yedek alma, negatif kontrol yedeği ve
geri alma, `--db`nin eski DSN kopyası ve yeni `--geri-al <yedek-dizini>` alt komutu bu TEK işlemden geçer — KOPYA YAZILMADI.
Reçeteler `sudo <betik> --geri-al <yedek>` gösterir.

M1 — `_tanitictan_oku` FIFO'ya çevrilen hedefte süresiz bloklamaz (`O_NONBLOCK` açılış, fstat ile normal dosya, sonra okuma).
M2 — dizin tanıtıcısı tutulurken dizin yeniden adlandırılırsa "başarı" denmez: yazım sonrası YOLDAKİ inode yazılanla kıyaslanır.
M3 — ön-denetim `url`/`dosya`/`api` satırlarını da `hedef-denetle` ile sorar (yazımdan, yedekten, `ALTER ROLE`dan ÖNCE).

ÇIKTI DİSİPLİNİ: iddialar bool'a indirgenir (`_iddia`); değerler SAHTEdir ve hiçbir çıktıda görünmemelidir.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import textwrap

import pytest

from tests.test_sir_rotasyon_v447 import BETIK, ESKI, YENI_NOUS, YENI_OR, _kos, _sahte_ortam
from tests.test_sir_yazim_yolu_v609 import ALAN, ESKI_ENV, YENI, _agac_imzasi, _iddia, _imza, _kalinti, _Sahne

KURBAN = "SAHTE-V611-KURBAN-0001"
GIZLI = "SAHTE-V611-GIZLI-0002"
_DEGERLER = (*ESKI.values(), YENI_NOUS, YENI_OR, YENI, ESKI_ENV, KURBAN, GIZLI)
GIRDI_OR = f"{YENI_NOUS}\n{YENI_OR}\n"


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

def _maskeli(metin: str) -> str:
    for d in _DEGERLER:
        metin = metin.replace(d, "<SAHTE-DEGER>")
    return metin


def _ozet(r: subprocess.CompletedProcess) -> str:
    return f"çıkış {r.returncode}\n--- stdout ---\n{_maskeli(r.stdout)[-3000:]}\n--- stderr ---\n{_maskeli(r.stderr)[-3000:]}"


def _sizinti_yok(r: subprocess.CompletedProcess) -> None:
    _iddia(not any(d in r.stdout + r.stderr for d in _DEGERLER), "bir SAHTE değer çıktıya düştü")


def _argv(kok: pathlib.Path) -> list[str]:
    return (kok / ".sahte/argv.log").read_text(encoding="utf-8").splitlines()


def _imzalar(kok: pathlib.Path) -> dict[str, tuple]:
    """Sahte kökün bütün girdileri (bağ İZLENMEDEN), şim günlükleri hariç."""
    return {k: v for k, v in _agac_imzasi(kok).items() if not k.startswith(".sahte")}


def _yedekler(kok: pathlib.Path) -> list[pathlib.Path]:
    return sorted((kok / "root").glob("sir-yedek-*"))


def _agacta_bayt_var(kok: pathlib.Path, deger: str) -> bool:
    return any(deger.encode() in p.read_bytes() for p in kok.rglob("*") if p.is_file() and not p.is_symlink())


def _kurban(tmp_path: pathlib.Path, ad: str = "kurban", icerik: str | None = None) -> pathlib.Path:
    d = tmp_path / "disari"
    d.mkdir(mode=0o755, exist_ok=True)
    k = d / ad
    k.write_text(icerik if icerik is not None else f"KURBAN_SATIRI={KURBAN}\n", encoding="utf-8")
    k.chmod(0o644)
    return k


def _sudo_kancasi(tmp_path: pathlib.Path, ortam: dict, kosul: str, eylem: str) -> pathlib.Path:
    """`sudo` çağrısı `kosul`u (argv listesi `a` üzerinde python ifadesi) sağladığında `eylem`i BİR kez yapar (işaret dosyası),
    sonra v447 sudo şimine AYNEN geçer. Yarış modeli UYGULAMADAN BAĞIMSIZ bir olaya bağlanır (yedek dizininin açılışı ·
    negatif kontrolün restart'ı): kancanın ateşlenmesi betiğin kopya YÖNTEMİNE bağlı olmasın — mutasyonda da ateşlensin."""
    isaret = tmp_path / "kanca_atesledi"
    d = tmp_path / "kanca_bin"
    d.mkdir()
    asil = str(tmp_path / "bin" / "sudo")
    govde = ("#!/usr/bin/env python3\nimport os, shutil, sys\na = sys.argv[1:]\n"
             f"ISARET = {str(isaret)!r}\n"
             "def _eylem():\n" + textwrap.indent(eylem.strip() + "\n", "    ") +
             f"if not os.path.exists(ISARET) and ({kosul}):\n"
             "    open(ISARET, 'w').close()\n"
             "    _eylem()\n"
             f"os.execv({asil!r}, [{asil!r}] + a)\n")
    (d / "sudo").write_text(govde, encoding="utf-8")
    (d / "sudo").chmod(0o755)
    ortam["PATH"] = f"{d}:{ortam['PATH']}"
    return isaret


def _yk_sure(yardimci: pathlib.Path, op: str, *args, kok: pathlib.Path, on: str = "",
             sure: float = 20.0) -> subprocess.CompletedProcess | None:
    """Gömülü yardımcıyı DOĞRUDAN koşar (v609 `_yk` + zaman aşımı). Askıda kalırsa None (çocuk öldürülür)."""
    kod = (on + "import runpy, sys\n"
           f"sys.argv = {[str(yardimci), op, *map(str, args)]!r}\n"
           f"runpy.run_path({str(yardimci)!r}, run_name='__main__')\n")
    ortam = {k: v for k, v in os.environ.items() if k != "SIR_ROT_KOK"}
    ortam["SIR_ROT_KOK"] = str(kok)
    try:
        return subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, env=ortam, timeout=sure)
    except subprocess.TimeoutExpired:
        return None


def _yardimci_metni() -> str:
    ham = BETIK.read_text(encoding="utf-8")
    bas = ham.index("<<'PY_SON'\n")
    return ham[bas:ham.index("\nPY_SON\n", bas)]


def _fonksiyon(metin: str, ad: str) -> str:
    g = metin[metin.index(f"def {ad}("):]
    return g[:g.index("\ndef ", 1)] if "\ndef " in g[1:] else g


def _kod_satirlari() -> list[str]:
    """Betiğin YORUM OLMAYAN satırları (kabuk ve gömülü python)."""
    return [s for s in BETIK.read_text(encoding="utf-8").splitlines() if s.strip() and not s.lstrip().startswith("#")]


# =================================================================================================
# A) `_negatif_geri_al` — öngörülebilir `.yeni` adı YOK, geri alma yardımcının fd-tabanlı çekirdeğinden geçer
# =================================================================================================

def test_A1_NEGATIF_KONTROL_geri_almasi_cp_ve_yan_dosya_ADI_KULLANMAZ_davranis_ESIT(tmp_path):
    """Operatörün koşacağı BİÇİM (`--openrouter`, iki anahtar — negatif kontrol iki kez geri alır). Davranış eşitliği: çıkış 0,
    hermes profilinin modu (0640) ve sahibi KORUNUR, yeni değer yazılır. Yeni sözleşme: argv günlüğünde `cp`/`mv` YOK ve hiçbir
    `.yeni` ADI geçmez; geri alma `kopyala <işlik>/nk-… <hedef>` ile, negatif kontrol yedeği `kopyala <hedef> <işlik>/nk-…` ile;
    ağaçta `.yeni` ya da geçici `.sir-rot-*` kalmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    bekci = kok / "home/ubuntu/.hermes/profiles/bekci/.env"
    bekci.chmod(0o640)
    once = bekci.stat()
    r = _kos(BETIK, ortam, "--openrouter", girdi=GIRDI_OR)
    _iddia(r.returncode == 0, _ozet(r))
    sonra = bekci.stat()
    _iddia((sonra.st_mode & 0o7777) == 0o640 and (sonra.st_uid, sonra.st_gid) == (once.st_uid, once.st_gid),
           "hermes profilinin modu/sahibi KORUNMADI")
    argv = _argv(kok)
    _iddia(not [s for s in argv if s.split()[:2] in (["sudo", "cp"], ["sudo", "mv"]) or s.split()[:1] in (["cp"], ["mv"])],
           "argv günlüğünde cp/mv var:\n" + "\n".join(s for s in argv if " cp " in f" {s} " or " mv " in f" {s} "))
    _iddia(not any(".yeni" in s for s in argv), "argv günlüğünde `.yeni` adı geçiyor")
    geri = [s for s in argv if " kopyala " in s and "/nk-" in s.split(" kopyala ", 1)[1].split()[0]]
    al = [s for s in argv if " kopyala " in s and "/nk-" in s.split(" kopyala ", 1)[1].split()[-1]]
    _iddia(len(geri) >= 2 and len(al) >= 2, f"negatif kontrol yedeği/geri alması `kopyala`dan geçmiyor: al={len(al)} geri={len(geri)}")
    _iddia(not list(kok.rglob("*.yeni")) and not _kalinti(kok), "ağaçta `.yeni` ya da geçici dosya kaldı")
    _sizinti_yok(r)


def test_A2_YENI_ADI_onceden_BAG_olarak_kurulursa_KURBAN_DOKUNULMAZ(tmp_path):
    """SALDIRI (inceleme §6 — her `--openrouter`in olağan yolu): ubuntu kendi dizinlerinde `secrets.json.yeni` ve
    `~/.hermes/.env.yeni` adlarını ÖNCEDEN kurbana bağlar. ESKİ yol: root `cp -p` bağı izler, kurbanı yedeğin içeriğiyle EZER,
    `mv -f` bağı hedefin yerine koyar (sonraki yazım bağda RED ile yarıda kalır). YENİ yol: `.yeni` adı hiç kullanılmaz —
    kurbanlar bayt/mod/inode aynı, bağlar yerinde ve dokunulmamış, hedefler düz dosya, rotasyon tamamlanır (çıkış 0)."""
    kok, ortam = _sahte_ortam(tmp_path)
    # Kurbanlar root'un dosyaları, kökün İÇİNDE (inceleme §6'nın örnekleri: `/root/.bashrc` · `/etc/profile.d/*.sh`).
    (kok / "etc/profile.d").mkdir(parents=True)
    k_env, k_json = kok / "root/.bashrc", kok / "etc/profile.d/meridian.sh"
    k_env.write_text(f"KURBAN_SATIRI={KURBAN}\n", encoding="utf-8")
    k_json.write_text(f"export KURBAN={KURBAN}\n", encoding="utf-8")
    baglar = {kok / "home/ubuntu/.hermes/.env.yeni": k_env, kok / "opt/meridian/state/secrets.json.yeni": k_json}
    for bag, hedef in baglar.items():
        bag.symlink_to(hedef)
    once = {k: _imza(k) for k in (k_env, k_json)}
    r = _kos(BETIK, ortam, "--openrouter", girdi=GIRDI_OR)
    for k, imza in once.items():
        _iddia(_imza(k) == imza, f"KURBAN DEĞİŞTİ (root bağı izledi): {k.name}")
    for bag, hedef in baglar.items():
        _iddia(bag.is_symlink() and os.readlink(bag) == str(hedef), f"`.yeni` bağına dokunuldu: {bag.name}")
    for h in (kok / "home/ubuntu/.hermes/.env", kok / "opt/meridian/state/secrets.json"):
        _iddia(h.is_file() and not h.is_symlink(), f"hedef bağa çevrildi: {h.name}")
    _iddia(r.returncode == 0, _ozet(r))
    _sizinti_yok(r)


def test_A3_GERI_ALMA_aninda_DIZIN_baga_cevrilirse_YAZIM_YOK_adli_ret_cikis_2(tmp_path):
    """Yarış: OPENROUTER negatif kontrolünün bozuk değerle restart'ı ANINDA ubuntu `profiles/sef`i ağacın DIŞINA taşır ve
    yerine bağ koyar. ESKİ yol: `cp -p … sef/.env.yeni` dizin bağını izler, geri alınan içerik ağaç DIŞINA yazılır. YENİ yol:
    o hedef için yazım YOK (zincirde bağ — adlı ret), öteki hedefler geri alınır, "GERİ ALMA BAŞARISIZ" + çıkış 2; dışarıdaki
    dosya geri alma tarafından yazılmadı (eski değer oraya DÖNMEDİ); taze anahtar hiçbir dosyaya girmedi."""
    kok, ortam = _sahte_ortam(tmp_path)
    disari = tmp_path / "disari"
    disari.mkdir(mode=0o755)
    sef, gercek = kok / "home/ubuntu/.hermes/profiles/sef", disari / "sef_gercek"
    isaret = _sudo_kancasi(tmp_path, ortam, 'a[:3] == ["systemctl", "restart", "apisix.service"]',
                           f"os.rename({str(sef)!r}, {str(gercek)!r})\nos.symlink({str(gercek)!r}, {str(sef)!r})")
    r = _kos(BETIK, ortam, "--openrouter", girdi=GIRDI_OR)
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    disaridaki = (gercek / ".env").read_text(encoding="utf-8")
    _iddia(ESKI["or"] not in disaridaki, "geri alma dizin BAĞINI izledi — ağaç dışındaki .env geri alındı")
    _iddia("sahte-" in disaridaki, "dışarıdaki .env bozuk değeri taşımıyor (pozitif kontrol: bozma yazımı oraya gitmişti)")
    _iddia(not list(disari.rglob("*.yeni")) and not _kalinti(disari), "ağaç dışında yan/geçici dosya doğdu")
    _iddia(r.returncode == 2 and "GERİ ALMA BAŞARISIZ" in r.stderr and "/home/ubuntu/.hermes/profiles/sef/.env" in r.stderr
           and "SEMBOLİK BAĞ" in r.stderr, _ozet(r))
    _iddia(not _agacta_bayt_var(kok, YENI_OR) and not _agacta_bayt_var(disari, YENI_OR), "taze anahtar bir dosyaya girdi")
    _iddia(_env_alan_ham(kok / "opt/apisix/.env-apisix", "OPENROUTER_AUTH") == f'"Bearer {ESKI["or"]}"',
           "öteki hedefler geri ALINMADI")
    _sizinti_yok(r)


def _env_alan_ham(yol: pathlib.Path, alan: str) -> str | None:
    for s in yol.read_text(encoding="utf-8").splitlines():
        if s.startswith(alan + "="):
            return s.split("=", 1)[1]
    return None


# =================================================================================================
# B) `_yedek_al` — kaynak bağ İZLENMEDEN okunur; bağsa yedek ALINMAZ, rotasyon BAŞLAMAZ · `kopyala` = bağ izlemeyen `cp -p`
# =================================================================================================

def test_B1_YEDEK_KAYNAGI_bag_ise_YEDEK_ALINMAZ_rotasyon_BASLAMAZ(tmp_path):
    """Yarış: ön-denetimden SONRA, yedek dizini açılırken (`install -d … sir-yedek-…`) ubuntu `karne/.env`i bir sır dosyasına
    bağlar. ESKİ yol: `sudo test -e` + `sudo cp -p` bağı izler, kurbanın içeriği yedeğe kopyalanır, rotasyon sürer ve karne'de
    yarıda kalır (referans + iki profil YENİ değerde). YENİ yol: "yedek ALINAMADI" + yol + "SEMBOLİK BAĞ", çıkış 1, HİÇBİR kopya
    yazılmadı, restart yok, kurbanın baytı yedekte YOK, geri alma reçetesi BASILMAZ (yedek alınmadı — beyan yalan olurdu)."""
    kok, ortam = _sahte_ortam(tmp_path)
    # Kurban kökün İÇİNDE bir root dosyası (üretimde çapa `/`dir: `/etc/...`): ağaç-dışı bir kurban çapa katmanına ("DIŞINDA")
    # da takılırdı ve kaynağı izleyen bir mutasyonu yalnız ileti düzeyinde ısırırdı.
    kurban = kok / "etc/meridian/gizli"
    kurban.write_text(f"GIZLI={GIZLI}\n", encoding="utf-8")
    kurban.chmod(0o400)
    karne = kok / "home/ubuntu/.hermes-botlar/profiles/karne/.env"
    isaret = _sudo_kancasi(tmp_path, ortam, 'a[:1] == ["install"] and "sir-yedek-" in a[-1]',
                           f"os.unlink({str(karne)!r})\nos.symlink({str(kurban)!r}, {str(karne)!r})")
    once = {k: v for k, v in _imzalar(kok).items() if "karne/.env" not in k}
    r = _kos(BETIK, ortam, "--tenant")
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    sonra = {k: v for k, v in _imzalar(kok).items() if "karne/.env" not in k and not k.startswith("root/")}
    _iddia(sonra == {k: v for k, v in once.items() if not k.startswith("root/")}, "bir kopya YAZILDI — rotasyon başlamıştı")
    _iddia(not _agacta_bayt_var(kok / "root", GIZLI), "kurbanın içeriği YEDEĞE kopyalandı (kaynak bağı izlendi)")
    _iddia(not (kok / ".sahte/systemctl.log").read_text(encoding="utf-8").strip(), "birim yeniden başlatıldı")
    _iddia(r.returncode == 1 and "yedek ALINAMADI" in r.stderr and "/home/ubuntu/.hermes-botlar/profiles/karne/.env" in r.stderr
           and "SEMBOLİK BAĞ" in r.stderr, _ozet(r))
    _iddia(">> GERİ ALMA" not in r.stderr, "yedek ALINMADAN geri alma reçetesi basıldı")
    _iddia(_imza(kurban)[0] == hashlib.sha256(f"GIZLI={GIZLI}\n".encode()).hexdigest(), "kurban değişti")
    _sizinti_yok(r)


@pytest.mark.parametrize("hal", ["kaynak_bag", "kaynak_dizin_bag", "kaynak_fifo_degil_dizin"])
def test_B2_KOPYALA_kaynak_bag_ya_da_normal_disi_ise_ADLI_RET_hedef_DOGMAZ(tmp_path, hal):
    """Yardımcı katmanı. (kaynak_bag) kaynak bir bağ; (kaynak_dizin_bag) kaynağın dizini bağ; (kaynak_fifo_degil_dizin) kaynak
    bir DİZİN (normal dosya değil). Hepsinde: çıkış ≠ 0, "KAYNAK" + "kopya YAPILMADI", hedef DOĞMAZ, kurban bayt-eşit."""
    s = _Sahne(tmp_path)
    # Kurban kökün İÇİNDE (üretimde çapa `/`): ağaç-dışı kurban çapa katmanına da takılır, bağ katmanını tek başına ölçmezdi.
    kurban = s.kok / "etc/meridian/kurban"
    kurban.write_text(f"{ALAN}={KURBAN}\n", encoding="utf-8")
    kaynak = s.env
    if hal == "kaynak_bag":
        kaynak = s.profil / ".env-bag"
        kaynak.symlink_to(kurban)
        neden = "SEMBOLİK BAĞ"
    elif hal == "kaynak_dizin_bag":
        bagli = s.kok / "home/ubuntu/.hermes/profiles/bagli"
        bagli.symlink_to(s.kok / "etc/meridian", target_is_directory=True)
        kaynak = bagli / "kurban"
        neden = "SEMBOLİK BAĞ"
    else:
        kaynak = s.profil / "dizin"
        kaynak.mkdir(mode=0o755)
        neden = "normal dosya değil"
    hedef = s.islik / "kopya"
    once = _imza(kurban)
    r = s.kos("kopyala", kaynak, hedef)
    _iddia(r.returncode != 0 and "KAYNAK" in r.stderr and neden in r.stderr and "kopya YAPILMADI" in r.stderr, _ozet(r))
    _iddia(not os.path.lexists(hedef) and _imza(kurban) == once and not _kalinti(s.islik), "hedef doğdu ya da kurban değişti")
    _sizinti_yok(r)


def test_B3_KOPYALA_cp_p_ESDEGERI_bayt_mod_sahip_ve_SESSIZ(tmp_path):
    """`cp -p` eşdeğeri: BAYT-EŞİT (CRLF ve UTF-8 dışı bayt dahil — metin kipi çevirseydi geri alma dosyayı değiştirirdi), mod
    (0640) ve sahip KAYNAĞIN, çıktı SESSİZ (altın izler stdout'u pinler). Var olan hedef ATOMİK yerine konur (yeni inode),
    hedef dizinde geçici dosya kalmaz. Ağaç içinden ağaç içine (yedek → üretim yolu yönü)."""
    s = _Sahne(tmp_path)
    ham = b"A=1\r\nB=\xff\xfe\n" + ESKI_ENV.encode() + b"\n"
    kaynak = s.islik / "yedek"
    kaynak.write_bytes(ham)
    kaynak.chmod(0o640)
    once_ino = s.env.stat().st_ino
    r = s.kos("kopyala", kaynak, s.env)
    st = s.env.lstat()
    _iddia(r.returncode == 0 and r.stdout == "", _ozet(r))
    _iddia(s.env.read_bytes() == ham and (st.st_mode & 0o7777) == 0o640 and stat.S_ISREG(st.st_mode)
           and (st.st_uid, st.st_gid) == (kaynak.stat().st_uid, kaynak.stat().st_gid) and st.st_ino != once_ino,
           "kopya bayt/mod/sahip eşit değil ya da yerine koyma atomik değil")
    _iddia(not _kalinti(s.profil, s.islik), "geçici dosya kaldı")
    _sizinti_yok(r)


# =================================================================================================
# C) M1 — FIFO'ya çevrilen hedef/kaynak süresiz BLOKLAMAZ
# =================================================================================================

#: Okuma açılışı ANINDA (denetim `lstat`ından SONRA) dosya bir FIFO ile değiştirilir. `O_RDONLY` açılışı yazar bekler; macOS
#: `mkfifo` `dir_fd` desteklemez — yol ile kurulur (inceleme sondası P1'in biçimi).
_FIFO_YARISI = '''import os
_o = os.open
def _open(p, flags, mode=0o777, *, dir_fd=None):
    if (dir_fd is not None and p == __AD__ and not flags & (os.O_CREAT | os.O_DIRECTORY)
            and not os.path.exists(__ISARET__)):
        open(__ISARET__, "w").close()
        os.unlink(__YOL__)
        os.mkfifo(__YOL__, 0o600)
    return _o(p, flags, mode, dir_fd=dir_fd)
os.open = _open
'''


@pytest.mark.parametrize("op", ["yaz-env", "kopyala"])
def test_C_FIFO_ya_cevrilen_dosya_ASKIDA_KALMAZ_adli_ret(tmp_path, op):
    """(yaz-env) oku-değiştir-yaz'ın eski içeriği; (kopyala) kopyanın kaynağı. ESKİ yol `O_RDONLY|O_NOFOLLOW` ile açar ve
    süresiz bekler (root rotasyonu ortada asılır — inceleme M1, sonda P1). YENİ yol: `O_NONBLOCK` açılış, fstat normal dosya
    DEĞİL → adlı ret, çıkış ≠ 0, ZAMAN AŞIMI YOK; hiçbir yazım yok."""
    s = _Sahne(tmp_path)
    isaret = tmp_path / "kanca_atesledi"
    on = (_FIFO_YARISI.replace("__AD__", repr(".env")).replace("__ISARET__", repr(str(isaret)))
          .replace("__YOL__", repr(str(s.env))))
    hedef = s.islik / "kopya"
    args = (s.env, ALAN, s.dgr, "koru", "koru", "-") if op == "yaz-env" else (s.env, hedef)
    r = _yk_sure(s.yardimci, op, *args, kok=s.kok, on=on, sure=20)
    _iddia(r is not None, "yardımcı FIFO'da ASKIDA KALDI (20 s zaman aşımı) — O_NONBLOCK yok")
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    _iddia(r.returncode != 0 and "normal dosya DEĞİL" in r.stderr and "YAPILMADI" in r.stderr, _ozet(r))
    _iddia(stat.S_ISFIFO(s.env.lstat().st_mode) and not os.path.lexists(hedef), "bir yazım yapıldı")
    _iddia(not _kalinti(s.profil, s.islik), "geçici dosya kaldı")
    _sizinti_yok(r)


# =================================================================================================
# D) M2 — dizin tanıtıcısı tutulurken dizin YENİDEN ADLANDIRILIRSA "başarı" denmez
# =================================================================================================

#: Yerine koyma ANINDA hedef dizin taşınır (`sef` → `sef_eski`) ve yerine eski `.env`in kopyasıyla YENİ bir `sef/` kurulur.
#: Yerine koyma tutulan (taşınmış) dizine iner; tanıtıcıya göre ölçüm (`_yazim_kusurlari` dir_fd) bunu GÖRMEZ.
_DIZIN_TASIMA = '''import os, shutil
_r = os.replace
def _replace(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
    if dst_dir_fd is not None and dst == __AD__ and not os.path.exists(__ISARET__):
        open(__ISARET__, "w").close()
        os.rename(__DIZIN__, __DIZIN__ + "_eski")
        os.mkdir(__DIZIN__, 0o755)
        shutil.copy2(os.path.join(__DIZIN__ + "_eski", __AD__), os.path.join(__DIZIN__, __AD__))
    return _r(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)
os.replace = _replace
'''


@pytest.mark.parametrize("op", ["yaz-env", "kopyala"])
def test_D_DIZIN_yeniden_adlandirilirsa_YOLDAKI_inode_kiyaslanir_BASARI_DENMEZ(tmp_path, op):
    """ESKİ yol: çıkış 0, yoldaki `.env` ESKİ (revoke edilecek) değerde kalır, taşınan dizindeki yeni değerde (inceleme M2,
    sonda P2). YENİ yol: yazım SONRASI yoldaki inode yazılanla kıyaslanır → "DOĞRULANAMADI" + "YOLDAKİ", çıkış ≠ 0; yoldaki
    dosya ESKİ hâliyle (başarı İDDİA EDİLMEDİ)."""
    s = _Sahne(tmp_path)
    isaret = tmp_path / "kanca_atesledi"
    on = (_DIZIN_TASIMA.replace("__AD__", repr(".env")).replace("__ISARET__", repr(str(isaret)))
          .replace("__DIZIN__", repr(str(s.profil))))
    eski = s.env.read_bytes()
    if op == "yaz-env":
        args = (s.env, ALAN, s.dgr, "koru", "koru", "-")
    else:
        kaynak = s.islik / "yedek"
        kaynak.write_text(f"{ALAN}={YENI}\n", encoding="utf-8")
        kaynak.chmod(0o640)
        args = (kaynak, s.env)
    r = _yk_sure(s.yardimci, op, *args, kok=s.kok, on=on, sure=60)
    _iddia(r is not None, "yardımcı ASKIDA KALDI")
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    _iddia(r.returncode != 0 and "DOĞRULANAMADI" in r.stderr and "YOLDAKİ" in r.stderr, _ozet(r))
    _iddia(s.env.read_bytes() == eski, "yoldaki dosya değişti — ölçüm modeli bozuk")
    _sizinti_yok(r)


# =================================================================================================
# E) M3 — ön-denetim `url` / `dosya` / `api` satırlarını da sorar: RED → yedek YOK, ALTER ROLE YOK, istem YOK
# =================================================================================================

_E_HALLERI = {
    # alt, bozulan yol, bozma
    "db_url_bag": ("db", "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL", "bag"),
    "db_url_sarkik_bag": ("db", "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL", "sarkik"),
    "db_url_dizin_grup_yazar": ("db", "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL", "grup"),
    "kapi_dosya_bag": ("kapi", "etc/meridian/kapi_apikey", "bag"),
    "openrouter_api_depo_bag": ("openrouter", "opt/meridian/state/secrets.json", "bag"),
}


@pytest.mark.parametrize("hal", sorted(_E_HALLERI))
def test_E_ON_DENETIM_url_dosya_api_REDDINDE_HICBIR_SEY_yazilmaz(tmp_path, hal):
    """Eski `--db` yolunda tablo sırası `sql` (ALTER ROLE) → `url`dir; url hedefinin yazım-anı RED'i ALTER'dan SONRA görülürdü:
    parola değişmiş, DSN eski → hindsight DB'den kopar (inceleme M3). YENİ: `hedef-denetle` url/dosya/api hedeflerinde de
    HİÇBİR yazımdan ÖNCE koşar → çıkış 1, "hedef REDDEDİLDİ: <yol>", yedek dizini DOĞMAZ, psql/ALTER yok, `kopyala` yok,
    restart yok, istem AÇILMAZ, sahte kök ve kurban bayt-eşit. (sarkık bağ: eskiden "hedef dosya YOK — --tohumla-sohbet"
    diye yanlış adlanıyordu — inceleme M8; artık bağ ADIYLA reddedilir.)"""
    alt, rel, bozma = _E_HALLERI[hal]
    kok, ortam = _sahte_ortam(tmp_path)
    hedef = kok / rel
    kurban = _kurban(tmp_path, "kurban", hedef.read_text(encoding="utf-8"))
    if bozma == "bag":
        hedef.unlink()
        hedef.symlink_to(kurban)
        neden = "SEMBOLİK BAĞ"
    elif bozma == "sarkik":
        hedef.unlink()
        hedef.symlink_to(tmp_path / "disari" / "yok")
        neden = "SEMBOLİK BAĞ"
    else:
        hedef.parent.chmod(0o775)
        neden = "YAZABİLİR"
    once_k, once_kurban = _imzalar(kok), _imza(kurban)
    try:
        r = _kos(BETIK, ortam, f"--{alt}", girdi=GIRDI_OR)
        sonra_k = _imzalar(kok)          # dizin modu imzanın parçasıdır: geri almadan ÖNCE ölçülür
    finally:
        hedef.parent.chmod(0o755)
    _iddia(r.returncode == 1 and f"hedef REDDEDİLDİ: /{rel}" in r.stderr and neden in r.stderr
           and "HİÇBİR ŞEY yazılmadı" in r.stderr, _ozet(r))
    _iddia(not _yedekler(kok), "yedek dizini AÇILDI — rotasyon ön-denetimden geçmişti")
    argv = _argv(kok)
    _iddia(not [s for s in argv if "psql" in s or " kopyala " in s or s.startswith("sudo install")],
           "ön-denetimden SONRAKİ bir adım koştu (psql / kopyala / install):\n" + "\n".join(argv))
    _iddia(not (kok / ".sahte/systemctl.log").read_text(encoding="utf-8").strip(), "restart yapıldı")
    _iddia("(boş = bu bacağı atla)" not in r.stderr, "istem AÇILDI — ön-denetim istemden SONRA")
    _iddia(sonra_k == once_k and _imza(kurban) == once_kurban, "sahte kök ya da kurban DEĞİŞTİ")
    _sizinti_yok(r)


def test_E2_ON_DENETIM_DB_url_hedefini_ALTER_ROLEdan_ve_yedekten_ONCE_sorar(tmp_path):
    """Sağlıklı `--db`: argv sırası `hedef-denetle <url>` → `install -d … sir-yedek` → `psql` (ALTER) — ön-denetim gerçekten
    koşuyor ve yerinde (v538 C7 altın izi aynı sırayı BİREBİR pinler)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--db")
    _iddia(r.returncode == 0, _ozet(r))
    argv = _argv(kok)

    def ilk(parca: str) -> int:
        return next((i for i, s in enumerate(argv) if parca in s), -1)
    sira = [ilk("hedef-denetle " + str(kok / "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL")),
            ilk("install -d -m 0700"), ilk("-u postgres psql")]
    _iddia(all(i >= 0 for i in sira) and sira == sorted(sira), f"sıra: {sira}\n" + "\n".join(argv))


# =================================================================================================
# F) REÇETELER + `--geri-al <yedek-dizini>` — aracın KENDİ güvenli geri alma yolu
# =================================================================================================

@pytest.mark.parametrize("alt", ["kapi", "dash", "tenant", "apisix-admin"])
def test_F1_RECETELER_kopya_ONERMEZ_geri_al_yolunu_gosterir(tmp_path, alt):
    """Başarılı koşumun iki reçetesi (stdout `>> geri alma:` · stderr `>> GERİ ALMA`) `sudo <betik> --geri-al <yedek>` der;
    `cp -p` / `sudo cp` YOK; değer basılmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, f"--{alt}")
    _iddia(r.returncode == 0, _ozet(r))
    yedek = _yedekler(kok)
    _iddia(len(yedek) == 1, f"yedek dizini sayısı {len(yedek)}")
    beklenen = f"sudo {BETIK} --geri-al {yedek[0]}"
    satir = [s for s in r.stdout.splitlines() if s.startswith(">> geri alma:")]
    _iddia(len(satir) == 1 and beklenen in satir[0], f"stdout reçetesi: {satir}")
    _iddia(beklenen in r.stderr and ">> GERİ ALMA (bu koşum YEDEK aldı" in r.stderr, _ozet(r))
    _iddia("cp -p" not in r.stdout + r.stderr and "sudo cp" not in r.stdout + r.stderr, "reçete kopya öneriyor")
    _sizinti_yok(r)


def test_F1s_STATIK_betikte_kopya_tabanli_root_yolu_ve_yan_dosya_adi_YOK():
    """Kabuk ve gömülü yardımcının YORUM OLMAYAN satırlarında `sudo cp` · `cp -p` · `mv -f` · `.yeni"` yok (dinamik çiviler
    yalnız koşturulan alt komutları görür); DOSYA geri alımı öneren her reçete satırı (alt komut sonu `>> geri alma:` · kasa
    reçetesinin `eski kanal:` adımı) `--geri-al $YEDEK` gösterir. (Genel `>> GERİ ALMA` reçetesi çok satırlı bir dizgedir —
    dinamik F1 ölçer.)"""
    kod = _kod_satirlari()
    yasak = [s.strip() for s in kod if re.search(r"\bsudo cp\b|\bcp -p\b|\bmv -f\b|\.yeni\"", s)]
    _iddia(not yasak, "kopya-tabanlı satır kaldı:\n" + "\n".join(yasak))
    recete = [s.strip() for s in kod if "echo" in s and (">> geri alma:" in s or "eski kanal: sudo" in s)]
    _iddia(len(recete) >= 10, f"reçete satırı çok az ({len(recete)}) — tarama kör")
    eksik = [s for s in recete if "--geri-al $YEDEK" not in s]
    _iddia(not eksik, "--geri-al göstermeyen reçete satırı:\n" + "\n".join(eksik))


def _kapi_sahnesi(tmp_path: pathlib.Path) -> tuple[pathlib.Path, dict, dict[str, tuple], pathlib.Path]:
    """`--kapi` koşulmuş dünya: (kök, ortam, rotasyon ÖNCESİ imzalar [kapi_apikey · .env-apisix], yedek dizini)."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "opt/apisix/.env-apisix").chmod(0o640)
    yollar = ("etc/meridian/kapi_apikey", "opt/apisix/.env-apisix")
    once = {y: _imza(kok / y) for y in yollar}
    r = _kos(BETIK, ortam, "--kapi")
    _iddia(r.returncode == 0, _ozet(r))
    _iddia(all(_imza(kok / y)[0] != once[y][0] for y in yollar), "rotasyon kopyaları YAZMADI (sahne)")
    return kok, ortam, once, _eskit(_yedekler(kok)[0], "20240101T000000Z")


def _eskit(yedek: pathlib.Path, damga: str) -> pathlib.Path:
    """Yedeği GEÇERLİ adla eski bir damgaya taşır. `--geri-al` (inceleme I2) yazmadan önce `sir-yedek-<ŞİMDİ>-<alt>` yedeği
    alır; girdi yedeği aynı saniyede doğmuşsa ad çakışır ve araç (doğru biçimde) "ZATEN VAR" ile durur — çivi saniye sınırına
    bağlı kalmasın (operatör koşumları saniyeler arayla gelir)."""
    alt = re.sub(r"^sir-yedek-\d{8}T\d{6}Z-", "", yedek.name)
    hedef = yedek.with_name(f"sir-yedek-{damga}-{alt}")
    yedek.rename(hedef)
    return hedef


def _satir_sonrasi(metin: str, parca: str) -> str:
    """`parca`yı taşıyan satırın HEMEN ardındaki satır (yoksa boş)."""
    s = metin.splitlines()
    i = next((k for k, x in enumerate(s) if parca in x), None)
    return s[i + 1] if i is not None and i + 1 < len(s) else ""


def test_F2_GERI_AL_yedekten_BAYT_MOD_ESIT_geri_koyar_KURU_yazmaz_RESTART_yok(tmp_path):
    """`--geri-al <yedek> --kuru` geri konacak yolları ADIYLA basar, gerçek koşumun ÖNCE yedek alacağını söyler, HİÇBİR ŞEY
    yazmaz (yedek dahil). `--geri-al <yedek>` ÖNCE mevcut hâli yeni bir `sir-yedek-<ts>-kapi`ye alır (inceleme I2 — aracın "her
    koşum önce yedekler" değişmezi; yolu stdout'ta; içeriği geri alma ÖNCESİ hâldir), sonra kapi_apikey ve `.env-apisix`i
    rotasyon ÖNCESİ baytına ve moduna döndürür (`cp -p` eşdeğeri), restart YAPMAZ (reçete basar), `cp` çağırmaz, değer basmaz;
    çıkış reçetesi o yeni yedekle GERİ ALMANIN GERİ ALINMASINI gösterir."""
    kok, ortam, once, yedek = _kapi_sahnesi(tmp_path)
    ara = _imzalar(kok)
    restart_once = (kok / ".sahte/systemctl.log").read_text(encoding="utf-8")
    rk = _kos(BETIK, ortam, "--geri-al", str(yedek), "--kuru")
    _iddia(rk.returncode == 0 and "geri konacak: /etc/meridian/kapi_apikey" in rk.stdout
           and "geri konacak: /opt/apisix/.env-apisix" in rk.stdout and "ÖNCE mevcut hâli yedekler" in rk.stdout, _ozet(rk))
    _iddia(_imzalar(kok) == ara and _yedekler(kok) == [yedek], "kuru koşum YAZDI ya da yedek aldı")
    argv_once = len(_argv(kok))
    r = _kos(BETIK, ortam, "--geri-al", str(yedek))
    yeni = [y for y in _yedekler(kok) if y != yedek]
    _iddia(len(yeni) == 1 and yeni[0].name.endswith("-kapi") and f"yedek dizini: {yeni[0]}" in r.stdout,
           f"geri almadan ÖNCE yeni yedek alınmadı ya da yolu basılmadı: {yeni}\n{_ozet(r)}")
    for y in ("etc/meridian/kapi_apikey", "opt/apisix/.env-apisix"):
        _iddia(hashlib.sha256((yeni[0] / y).read_bytes()).hexdigest() == ara[y][1],
               f"yeni yedekteki {y} geri alma ÖNCESİ hâl değil")
    _iddia(">> GERİ ALMA (bu koşum YEDEK aldı" in r.stderr and f"--geri-al {yeni[0]}" in r.stderr
           and "sonra yeniden başlat: apisix.service meridian.service" in r.stderr
           and "(birim listesi ölçülemedi)" not in r.stderr,
           "çıkış reçetesi geri almanın geri alınmasını (ve geri alınan alt komutun birimlerini) göstermiyor")
    _iddia(r.returncode == 0 and "geri kondu: /etc/meridian/kapi_apikey" in r.stdout
           and "geri kondu: /opt/apisix/.env-apisix" in r.stdout and "sonra yeniden başlat:" in r.stdout, _ozet(r))
    for y, imza in once.items():
        st = (kok / y).lstat()
        _iddia(_imza(kok / y)[0] == imza[0] and (st.st_mode & 0o7777) == imza[1] and stat.S_ISREG(st.st_mode),
               f"{y}: bayt/mod rotasyon ÖNCESİNE dönmedi")
    _iddia((kok / ".sahte/systemctl.log").read_text(encoding="utf-8") == restart_once, "--geri-al birim yeniden başlattı")
    yeni_argv = _argv(kok)[argv_once:]
    _iddia(not [s for s in yeni_argv if s.split()[:2] == ["sudo", "cp"]] and any(" kopyala " in s for s in yeni_argv),
           "--geri-al `kopyala`dan geçmiyor ya da cp çağırıyor")
    _sizinti_yok(rk)
    _sizinti_yok(r)


@pytest.mark.parametrize("hal", ["kok_disi", "bilinmeyen_alt", "dizin_bag", "arguman_yok", "vault_ile"])
def test_F3_GERI_AL_yalniz_YEDEK_DIZINI_kabul_eder_HICBIR_SEY_yazmadan_reddeder(tmp_path, hal):
    """(kok_disi) yedek kökünün (`/root/sir-yedek-*`) dışı — GEÇERLİ adlı ama ubuntu'nun evinde, saldırganın içeriğini taşıyan
    bir "yedek" (kapı kalksa `kopyala` onu ubuntu sahipliğiyle `/etc/meridian/kapi_apikey`e yazardı: zincir ubuntu'nun, izinli
    {root, kaynağın sahibi}); (bilinmeyen_alt) adı kopya tablosunda olmayan alt komut taşıyor;
    (dizin_bag) yedek dizini bir bağ; (arguman_yok) dizin verilmedi; (vault_ile) `--vault` ile verildi. Hepsinde çıkış 1 ve
    sahte kök bayt-eşit."""
    kok, ortam, _, yedek = _kapi_sahnesi(tmp_path)
    once = _imzalar(kok)
    if hal == "kok_disi":
        sahte = kok / "home/ubuntu/sir-yedek-20260101T000000Z-kapi"
        (sahte / "etc/meridian").mkdir(parents=True)
        (sahte / "etc/meridian/kapi_apikey").write_text(KURBAN + "\n", encoding="utf-8")
        once = _imzalar(kok)
        args = ["--geri-al", str(sahte)]
        metin = "yedek dizini DEĞİL"
    elif hal == "bilinmeyen_alt":
        sahte = kok / "root/sir-yedek-20260101T000000Z-yok"
        sahte.mkdir(mode=0o700)
        once = _imzalar(kok)
        args = ["--geri-al", str(sahte)]
        metin = "kopya tablosunda"
    elif hal == "dizin_bag":
        bag = kok / "root/sir-yedek-20260101T000000Z-kapi"
        bag.symlink_to(yedek, target_is_directory=True)
        once = _imzalar(kok)
        args = ["--geri-al", str(bag)]
        metin = "SEMBOLİK BAĞ"
    elif hal == "arguman_yok":
        args = ["--geri-al"]
        metin = "YEDEK DİZİNİ ister"
    else:
        args = ["--geri-al", str(yedek), "--vault"]
        metin = "--geri-al"
    r = _kos(BETIK, ortam, *args)
    _iddia(r.returncode == 1 and metin in r.stderr, _ozet(r))
    _iddia(_imzalar(kok) == once, "reddedilen --geri-al bir dosya YAZDI")
    _sizinti_yok(r)


def test_F4a_GERI_AL_hedef_ONCEDEN_bagsa_yedek_ALINAMAZ_HICBIR_SEY_yazilmaz(tmp_path):
    """Rotasyondan sonra `.env-apisix` bir kurbana bağ olur. `--geri-al` yazmadan ÖNCE mevcut hâli yedekler (inceleme I2) ve
    yedeğin kaynağı bağ izlenmeden okunur: bağlı hedef "yedek ALINAMADI" + yol + "SEMBOLİK BAĞ" ile durdurur (çıkış 1) — HİÇBİR
    dosya geri konmaz (kapi_apikey de YENİ değerde kalır; yarım geri alma yok), kurban bayt-eşit, bağ yerinde, reçete basılmaz."""
    kok, ortam, once, yedek = _kapi_sahnesi(tmp_path)
    apisix = kok / "opt/apisix/.env-apisix"
    kurban = _kurban(tmp_path)
    apisix.unlink()
    apisix.symlink_to(kurban)
    once_k, ara = _imza(kurban), _imza(kok / "etc/meridian/kapi_apikey")
    r = _kos(BETIK, ortam, "--geri-al", str(yedek))
    _iddia(r.returncode == 1 and "yedek ALINAMADI: /opt/apisix/.env-apisix" in r.stderr and "SEMBOLİK BAĞ" in r.stderr, _ozet(r))
    _iddia(_imza(kurban) == once_k and apisix.is_symlink(), "kurban yazıldı ya da bağ ezildi")
    _iddia(_imza(kok / "etc/meridian/kapi_apikey") == ara, "yedek alınamadan bir hedef geri KONDU")
    _iddia(">> GERİ ALMA" not in r.stderr, "yedek ALINMADAN geri alma reçetesi basıldı")
    _sizinti_yok(r)


def test_F4b_GERI_AL_yazim_aninda_baga_cevrilen_hedef_ADLA_reddedilir_otekiler_geri_konur(tmp_path):
    """Yarış: ön yedekten SONRA, ilk geri koyma anında `.env-apisix` bir kurbana bağ olur. O hedef için yazım YOK ("geri
    KONAMADI" + yol + "SEMBOLİK BAĞ"), kurban bayt-eşit, öteki hedef (kapi_apikey) geri konur, çıkış 1 (bilinen arıza); ön yedek
    ALINMIŞTIR ve çıkış reçetesi onu gösterir."""
    kok, ortam, once, yedek = _kapi_sahnesi(tmp_path)
    apisix = kok / "opt/apisix/.env-apisix"
    kurban = _kurban(tmp_path)
    once_k = _imza(kurban)
    isaret = _sudo_kancasi(
        tmp_path, ortam,
        f'len(a) >= 5 and a[2] == "kopyala" and a[3] == {str(yedek / "etc/meridian/kapi_apikey")!r}',
        f"os.unlink({str(apisix)!r})\nos.symlink({str(kurban)!r}, {str(apisix)!r})")
    r = _kos(BETIK, ortam, "--geri-al", str(yedek))
    _iddia(isaret.exists(), "yarış kancası ATEŞLENMEDİ — çivi kör (pozitif kontrol)")
    _iddia(r.returncode == 1 and "geri KONAMADI: /opt/apisix/.env-apisix" in r.stderr and "SEMBOLİK BAĞ" in r.stderr, _ozet(r))
    _iddia(_imza(kurban) == once_k and apisix.is_symlink(), "kurban yazıldı ya da bağ ezildi")
    _iddia(_imza(kok / "etc/meridian/kapi_apikey")[0] == once["etc/meridian/kapi_apikey"][0], "öteki hedef geri KONMADI")
    yeni = [y for y in _yedekler(kok) if y != yedek]
    _iddia(len(yeni) == 1 and f"--geri-al {yeni[0]}" in r.stderr, "ön yedek alınmadı ya da reçete onu göstermiyor")
    _sizinti_yok(r)


def test_F6_GERI_AL_cok_anahtarli_dosya_BUTUN_doner_KURU_baska_alanlari_ADLANDIRIR_GERI_ALMA_GERI_ALINABILIR(tmp_path):
    """İnceleme I2 senaryosu (sonda S2): `--kapi` → `--openrouter` (`.env-apisix`e YENİ OpenRouter değeri) → `--geri-al <kapi
    yedeği>`. Dosya BÜTÜN döner, yani OpenRouter alanları da eskiye döner. (a) `--kuru` bunu ÖNCEDEN söyler: `.env-apisix` için
    "BAŞKA alanlar" satırı OPENROUTER_API_KEY ve OPENROUTER_AUTH ADLARINI taşır, kapı'nın kendi alanını (BOT_KEY_MERIDIAN)
    taşımaz; değer basılmaz. (b) Gerçek koşum ÖNCE mevcut hâli yedekler: yeni yedekteki `.env-apisix` geri alma ÖNCESİ baytlardır
    (YENİ OpenRouter değeri dahil). (c) O yedekle `--geri-al` geri almayı GERİ ALIR: `.env-apisix` geri alma öncesi baytlarına
    döner (iptal edilmiş/bayat anahtar kalıcı olmaz)."""
    kok, ortam = _sahte_ortam(tmp_path)
    apisix = kok / "opt/apisix/.env-apisix"
    r1 = _kos(BETIK, ortam, "--kapi")
    _iddia(r1.returncode == 0, _ozet(r1))
    kapi_yedek = _eskit(_yedekler(kok)[0], "20240101T000000Z")
    r2 = _kos(BETIK, ortam, "--openrouter", girdi=GIRDI_OR)
    _iddia(r2.returncode == 0 and YENI_OR in apisix.read_text(encoding="utf-8"), _ozet(r2))
    once_geri = apisix.read_bytes()
    rk = _kos(BETIK, ortam, "--geri-al", str(kapi_yedek), "--kuru")
    uyari = _satir_sonrasi(rk.stdout, "geri konacak: /opt/apisix/.env-apisix")
    _iddia(rk.returncode == 0 and "BAŞKA alanlar" in uyari and "OPENROUTER_API_KEY" in uyari and "OPENROUTER_AUTH" in uyari
           and "BOT_KEY_MERIDIAN" not in uyari and "APISIX_ADMIN_KEY" not in uyari, f"kuru uyarısı: {uyari!r}\n{_ozet(rk)}")
    oncekiler = set(_yedekler(kok))
    r = _kos(BETIK, ortam, "--geri-al", str(kapi_yedek))
    yeni = sorted(set(_yedekler(kok)) - oncekiler)
    _iddia(r.returncode == 0 and len(yeni) == 1 and f"yedek dizini: {yeni[0]}" in r.stdout, _ozet(r))
    _iddia((yeni[0] / "opt/apisix/.env-apisix").read_bytes() == once_geri, "yeni yedek geri alma ÖNCESİ hâli taşımıyor")
    _iddia(YENI_OR not in apisix.read_text(encoding="utf-8"), "geri alma dosyayı BÜTÜN döndürmedi (sahne varsayımı)")
    geri_geri = _eskit(yeni[0], "20240102T000000Z")
    rr = _kos(BETIK, ortam, "--geri-al", str(geri_geri))
    _iddia(rr.returncode == 0 and apisix.read_bytes() == once_geri, f"geri alma GERİ ALINAMADI\n{_ozet(rr)}")
    for x in (rk, r, rr):
        _sizinti_yok(x)


def test_F7_GERI_AL_KURU_motor_deposunda_degismis_BASKA_anahtarlari_ADLANDIRIR(tmp_path):
    """Motor deposu (`state/secrets.json`) çok anahtarlıdır (Telegram/Alpaca/FMP kimlikleri de orada yaşar). `--openrouter`
    yedeğinden sonra motor depoya YENİ bir anahtar yazarsa `--geri-al --kuru` onun ADINI "BAŞKA alanlar" satırında söyler (geri
    almada silinir); rotasyonun kendi anahtarını (NOUS_API_KEY) saymaz; değer basılmaz, hiçbir şey yazılmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    r1 = _kos(BETIK, ortam, "--openrouter", girdi=GIRDI_OR)
    _iddia(r1.returncode == 0, _ozet(r1))
    yedek = _eskit(_yedekler(kok)[0], "20240101T000000Z")
    depo = kok / "opt/meridian/state/secrets.json"
    veri = json.loads(depo.read_text(encoding="utf-8"))
    veri["TELEGRAM_BOT_TOKEN"] = GIZLI
    depo.write_text(json.dumps(veri) + "\n", encoding="utf-8")
    once = _imzalar(kok)
    rk = _kos(BETIK, ortam, "--geri-al", str(yedek), "--kuru")
    uyari = _satir_sonrasi(rk.stdout, "geri konacak: /opt/meridian/state/secrets.json")
    _iddia(rk.returncode == 0 and "BAŞKA alanlar" in uyari and "TELEGRAM_BOT_TOKEN" in uyari and "NOUS_API_KEY" not in uyari,
           f"kuru uyarısı: {uyari!r}\n{_ozet(rk)}")
    _iddia(_imzalar(kok) == once and _yedekler(kok) == [yedek], "kuru koşum YAZDI ya da yedek aldı")
    _sizinti_yok(rk)


@pytest.mark.parametrize("kip", ["gercek", "kuru"])
def test_F8_GERI_AL_SIFIR_dosyada_BASARI_DEMEZ_cikis_1_yedek_YOK(tmp_path, kip):
    """İnceleme M5. GEÇERLİ adlı ama alt komutun tablo yollarının HİÇBİRİNİ taşımayan bir yedek (yanlış dizin): eskiden "geri
    alma tamam: 0 dosya", çıkış 0. Şimdi çıkış 1 + "geri konacak dosya YOK" — bir otomasyon ya da operatör "geri alındı" sanıp
    birimleri yeniden başlatmasın (uydurma yasağı: olmayan bir geri almayı başarı saymak). Ön yedek ALINMAZ (yapılacak iş yok),
    hiçbir şey yazılmaz; kuru koşum da aynı hükmü verir (gerçek koşumun ön-bakışı)."""
    kok, ortam = _sahte_ortam(tmp_path)
    bos = kok / "root/sir-yedek-20240101T000000Z-dash"
    bos.mkdir(mode=0o700)
    once = _imzalar(kok)
    r = _kos(BETIK, ortam, "--geri-al", str(bos), *(("--kuru",) if kip == "kuru" else ()))
    _iddia(r.returncode == 1 and "geri konacak dosya YOK" in r.stderr, _ozet(r))
    _iddia(_imzalar(kok) == once and _yedekler(kok) == [bos], "sıfır dosyalı geri alma yazdı ya da yedek aldı")
    _sizinti_yok(r)


def test_F5_KULLANIM_basligi_geri_al_satirini_sudo_ile_belgeler():
    """K1b biçimi: operatörün yapıştıracağı satır başlıkta (`docs/RUNBOOK.md` bu başlıktan üretilir — Rol-1 yeniden üretir)."""
    baslik = BETIK.read_text(encoding="utf-8").split("set -euo pipefail", 1)[0]
    _iddia("sudo ./sir_rotasyon.sh --geri-al <" in baslik, "KULLANIM satırı yok: --geri-al")
    _iddia("cp -p" not in baslik, "başlık hâlâ `cp -p` reçetesi/yedeği anlatıyor")


# =================================================================================================
# G) TEK GÖVDE — kopya yolu yazım çekirdeğinin KENDİSİDİR (brief: "KOPYA YAZMA")
# =================================================================================================

def test_G_STATIK_kopyala_ORTAK_CEKIRDEKTEN_gecer_yeni_acilis_yazim_YOK():
    yardimci = _yardimci_metni()
    _iddia(yardimci.count("def _kopyala(") == 1, "`_kopyala` TEK tanım değil")
    govde = _fonksiyon(yardimci, "_kopyala")
    for parca in ("_hedef_ac(", "_tanitictan_oku(", "_atomik_yaz("):
        _iddia(parca in govde, f"`_kopyala` ortak çekirdekten geçmiyor: {parca}")
    for yasak in ("os.open(", "open(", "shutil", "os.replace(", "os.fchown(", "os.fchmod("):
        _iddia(yasak not in govde.replace("_tanitictan_oku(", "").replace("_hedef_ac(", ""),
               f"`_kopyala` kendi açılış/yazımını yapıyor: {yasak}")
    oku = _fonksiyon(yardimci, "_tanitictan_oku")
    _iddia("O_NONBLOCK" in oku and "S_ISREG" in oku, "`_tanitictan_oku` O_NONBLOCK + normal dosya denetimi taşımıyor (M1)")

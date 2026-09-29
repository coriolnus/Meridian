"""tests/test_iki_kanal_kapanisi_v590.py — TSK-064 İKİ-KANAL KAPANIŞI (2026-09-29): Hindsight kiracı anahtarı ve
hindsight-cp ortam dosyası YALNIZ Vault kanalından.

NUMARA: `ls tests | grep _v59` boş (2026-09-29; ana checkout + tek worktree `tsk064-ikikanal` tarandı).

BAĞLAM (Rol-1 brief'i + ROADMAP TSK-064 2026-09-29 07:5xZ tüketici haritası). İki eski kopya yaşıyordu:
  · `/opt/hindsight/.key` (0600 ubuntu) — kiracı anahtarının düz kopyası; TEK okuyucusu Rol-1 araçları
    `deploy/hindsight/hafiza_sor.sh` + `sayfa_oku.sh` (A1'de `~/bin` bağları). Vault render hedefi
    `/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY` 0400 root → ubuntu doğrudan okuyamaz.
  · `/opt/hindsight/.env-cp` (0600 root) — hindsight-cp temel biriminin `EnvironmentFile=`ı; Vault yan dosyası
    `.env-cp.vault` 2026-09-14'ten beri AYNI iki değişkeni taşıyor ve drop-in 50 onu SONRA (opsiyonel) okuyor.
KARARLAR (Rol-1): (1) `.env-cp` → dash-token Faz-2 emsali drop-in (`51-env-cp-kaldir.conf`: boş `EnvironmentFile=`
sıfırlar + `.env-cp.vault` ZORUNLU, tiresiz); temel birime DOKUNULMAZ. (2) `.key` → araçlar anahtarı
`sudo -n cat <render hedefi>` ALT SÜRECİNİN BORUSUNDAN okur (Vault Agent `template`inde sahiplik alanı yok, `exec
chown` DİLİM-3'te emekli; ACL her atomik render'da kaybolur). `HAFIZA_ANAHTAR_DOSYASI` ezmesi KORUNUR. (3) rotasyon
tablosu + envanter ATOMİK (v447 `--kopyalar` ↔ envanter eşitliği). Eski dosyaların KALDIRILMASI kodun işi değil,
operatör adımıdır (deploy/oracle-a1/RUNBOOK.md sonu).

BÖLÜMLER
  A  drop-in 51 — sıfırlama + tek ZORUNLU yan dosya · birleşik liste · A0 rolü kurar · temel birim dokunulmadı ·
     systemd kompozisyon modeli (ara hâl: eski dosya dururken değer KASADAN; yan dosya yoksa birim AÇILMAZ)
  B  araçlar — varsayılan kaynak sudo borusu (argv'de yalnız YOL; değer argv/ortam/çıktıda YOK) · sudo düşerse
     çıkış 1, istek/kayıt yok · ezme verilince sudo ÇAĞRILMAZ · CR/LF kırpması aynı
  C  rotasyon + envanter — tabloda emekli yol yok · envanter `emekli_kopyalar` üç satır, tarihli · kasa
     `kopya_kaynaklari` temiz · betiğin emekli listesi ↔ envanter · `--envanter` emekli kopyayı bağırır/YOK der ·
     `--tenant` ve `--cp --vault` eski dosyalara YAZMAZ · `dosyalar:`/spec `.env-cp` satırı ÇIKTI (A1'den kaldırıldı
     2026-09-29 11:32Z), emekli kayıtlar kaldırma anını + yedek dizinini taşır
  D  RUNBOOK operatör adımı — dosyanın SONUNDA, sıra: A0 → restart → doğrulama → yedek → kaldırma → son doğrulama;
     kaldırma TAŞIMADIR (`<yedek>/orijinal/`, kalıcı silme yok) ve UYGULANDI notu envanterle ayrışmaz

SIR DEĞERİ YOK: bütün değerler SAHTE (v447/v547 tohumları). Çıktı disiplini: iddia mesajları süreç tablosunu,
ortamı ya da değeri basmaz (yalnız ad/yol).
"""
from __future__ import annotations

import glob
import os
import pathlib
import re
import subprocess
import sys

import pytest
import yaml

from tests import test_cp_rotasyon_v556 as v556
from tests import test_sir_rotasyon_v447 as v447
from tests.test_hafiza_okuma_kaydi_v547 import (  # noqa: F401 — `sunucu` fikstürü ithalle kaydolur
    HAFIZA_SOR,
    SAHTE_ANAHTAR,
    SAYFA_OKU,
    SORU,
    _kos,
    _ortam,
    sunucu,
)
from tests.test_hindsight_anahtar_argv_v552 import _bolumler, _torun_argvleri
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _yonergeler

KOK = pathlib.Path(__file__).resolve().parents[1]
DEPLOY = KOK / "deploy"
ANSIBLE = DEPLOY / "ansible"
DEFAULTS = ANSIBLE / "roles" / "meridian_a1" / "defaults" / "main.yml"
ENVANTER = DEPLOY / "sir_envanteri.yaml"
SPEC = KOK / "docs" / "TASARIM-SIR-YOL1-2026-09-03.md"
RUNBOOK = DEPLOY / "oracle-a1" / "RUNBOOK.md"
BETIK = v447.BETIK
CP_BIRIM = DEPLOY / "hindsight" / "hindsight-cp.service"
CP_DROPIN_DIZIN = DEPLOY / "hindsight" / "hindsight-cp.service.d"
DROPIN_51 = CP_DROPIN_DIZIN / "51-env-cp-kaldir.conf"

KAYNAK = "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"   # Vault Agent render hedefi (0400 root)
ESKI_KEY = "/opt/hindsight/.key"
ENV_CP = "/opt/hindsight/.env-cp"
ENV_CP_VAULT = "/opt/hindsight/.env-cp.vault"
KANON_CP = "/etc/meridian/hindsight_cp_access_key"
EMEKLI_YOLLAR = frozenset({ESKI_KEY, ENV_CP})
EMEKLI_TARIH = "2026-09-29"
#: Kapanışın emekli ettiği ÜÇ rotasyon satırı — (alt komut, sır, tür, yol, alan).
BEKLENEN_EMEKLI = {
    ("tenant", "HINDSIGHT_API_TENANT_API_KEY", "dosya", ESKI_KEY, None),
    ("tenant", "HINDSIGHT_API_TENANT_API_KEY", "env", ENV_CP, "HINDSIGHT_CP_DATAPLANE_API_KEY"),
    ("cp", "HINDSIGHT_CP_ACCESS_KEY", "env", ENV_CP, "HINDSIGHT_CP_ACCESS_KEY"),
}
#: `rotasyon_kopyalari.kopyalar` satır şeması (v447 A4) + emekliliğin iki alanı + A1'den kaldırmanın iki alanı
#: (`kaldirildi` · `yedek_dizini` — 2026-09-29 11:32Z uygulamasından beri; YALNIZ yol/zaman, değer yok).
EMEKLI_SEMA = {"alt_komut", "sir", "tur", "yol", "alan", "mod", "sahip", "tuketici", "onek", "not", "emekli",
               "kaldirildi", "yedek_dizini"}
#: A1 UYGULAMASI (Rol-1 olgusu, 2026-09-29 11:32Z): iki eski dosya `rm` ile DEĞİL, root-only yedek dizininin
#: `orijinal/` alt dizinine TAŞINARAK kaldırıldı (kalıcı silme yok). Elle yazılı DIŞ ÇAPA (v439 E0 gerekçesi):
#: envanter ve RUNBOOK birbirinden türetilseydi ikisi birlikte bayatlayıp "uyuşuyor" derdi.
KALDIRMA_ANI = "2026-09-29 11:32Z"
YEDEK_DIZINI = "/root/sir-yedek-20260929T113217Z-ikikanal/"


def _envanter() -> dict:
    return yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))


# =================================================================================================
# A) DROP-IN 51 — hindsight-cp YALNIZ `.env-cp.vault`
# =================================================================================================

def _etkin_env_dosyalari(dropinler: list[pathlib.Path] | None = None) -> list[str]:
    """systemd'nin BİRLEŞİK `EnvironmentFile=` listesi: temel birim, sonra drop-in'ler AD sırasıyla; BOŞ atama
    o ana kadar biriken listeyi SIFIRLAR (systemd.exec(5) — liste yönergesi)."""
    kaynaklar = [CP_BIRIM, *(sorted(CP_DROPIN_DIZIN.glob("*.conf")) if dropinler is None else dropinler)]
    liste: list[str] = []
    for p in kaynaklar:
        for bolum, anahtar, deger in _yonergeler(p.read_text(encoding="utf-8")):
            if bolum == "Service" and anahtar == "EnvironmentFile":
                liste = [] if not deger else [*liste, deger]
    return liste


def test_A1_dropin_51_YALNIZ_sifirlama_ve_ZORUNLU_yan_dosya():
    """Brief: `[Service]` · boş `EnvironmentFile=` · `EnvironmentFile=/opt/hindsight/.env-cp.vault` — SIRAYLA ve
    başka HİÇBİR yönerge yok (ExecStart'a dokunan bir drop-in v554/v587 komut satırı sözleşmelerini açardı)."""
    assert DROPIN_51.exists(), "drop-in 51 yok"
    assert _yonergeler(DROPIN_51.read_text(encoding="utf-8")) == [
        ("Service", "EnvironmentFile", ""),
        ("Service", "EnvironmentFile", ENV_CP_VAULT),
    ]


def test_A2_BIRLESIK_liste_TEK_ve_ZORUNLU_yan_dosya():
    """Asıl ölçüm: birim + BÜTÜN drop-in'ler birleşince CP'nin ortam kaynağı TEK dosyadır ve tiresizdir (yoksa
    birim AÇILMAZ — sessiz anahtarsız açılış yerine gürültülü arıza)."""
    assert _etkin_env_dosyalari() == [ENV_CP_VAULT]


def test_A3_POZITIF_KONTROL_51_olmadan_eski_kanal_GORUNUR():
    """Model kör değil: 51 çıkarılınca eski iki-kanal hâli (temel `.env-cp` + 50'nin opsiyonel yan dosyası) aynı
    ayrıştırıcıyla GERİ görünür — A2 yanlış sebeple yeşil olamaz."""
    digerleri = [p for p in sorted(CP_DROPIN_DIZIN.glob("*.conf")) if p.name != DROPIN_51.name]
    assert _etkin_env_dosyalari(digerleri) == [ENV_CP, "-" + ENV_CP_VAULT]


def test_A4_TEMEL_BIRIM_ve_50_DOKUNULMADI():
    """Brief: temel birime DOKUNULMAZ (F9 içerik aynası + depo–canlı ayrıklığı; dash-token emsali) — kapanış
    YALNIZ drop-in'dir. 50 tarihsel kayıt olarak kalır, yönergesi değişmez."""
    temel = [(a, d) for b, a, d in _yonergeler(CP_BIRIM.read_text(encoding="utf-8")) if a == "EnvironmentFile"]
    assert temel == [("EnvironmentFile", ENV_CP)], temel
    elli = CP_DROPIN_DIZIN / "50-vault-yan-dosya.conf"
    assert _yonergeler(elli.read_text(encoding="utf-8")) == [("Service", "EnvironmentFile", "-" + ENV_CP_VAULT)]


def test_A5_A0_ROLU_51i_KURAR():
    """A1'e yol: A0 rolü (`site.yml` → `dropinler.yml`). Dizin `dropin_dizinleri`nde, glob `dropin_kaynaklari`nda
    — yeni satır GEREKMEZ (v451 iki yönlü eşitlik). Glob, rolün kendi sözdizimiyle çözülür."""
    d = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))
    assert "hindsight-cp.service.d" in d["dropin_dizinleri"]
    bulunan: set[pathlib.Path] = set()
    for desen in d["dropin_kaynaklari"]:
        bulunan |= {pathlib.Path(p).resolve() for p in glob.glob(desen.replace("{{ playbook_dir }}", str(ANSIBLE)))}
    assert DROPIN_51.resolve() in bulunan, "A0 rolünün glob'u 51'i KAPSAMIYOR"


def _systemd_ortami(liste: list[str], kok: pathlib.Path) -> dict[str, str] | None:
    """Sırayla oku, aynı anahtarda SONRAKİ kazanır; `-` önekli yok dosya atlanır; zorunlu dosya yoksa birim
    AÇILMAZ → None (systemd: "Failed to load environment files")."""
    ortam: dict[str, str] = {}
    for girdi in liste:
        yol = kok / girdi.lstrip("-").lstrip("/")
        if not yol.exists():
            if girdi.startswith("-"):
                continue
            return None
        for s in yol.read_text(encoding="utf-8").splitlines():
            if "=" in s and not s.lstrip().startswith("#"):
                k, v = s.split("=", 1)
                ortam[k.strip()] = v.strip()
    return ortam


def _cp_dosyalari(kok: pathlib.Path, *, eski: bool, yan: bool) -> None:
    (kok / "opt/hindsight").mkdir(parents=True, exist_ok=True)
    if eski:
        (kok / ENV_CP.lstrip("/")).write_text("HINDSIGHT_CP_ACCESS_KEY=SAHTE-BAYAT-ERISIM\n"
                                              "HINDSIGHT_CP_DATAPLANE_API_KEY=SAHTE-BAYAT-KIRACI\n", encoding="utf-8")
    if yan:
        (kok / ENV_CP_VAULT.lstrip("/")).write_text("HINDSIGHT_CP_ACCESS_KEY=SAHTE-KASA-ERISIM\n"
                                                    "HINDSIGHT_CP_DATAPLANE_API_KEY=SAHTE-KASA-KIRACI\n",
                                                    encoding="utf-8")


def test_A6_MODEL_ARA_HAL_eski_dosya_DURURKEN_deger_KASADAN(tmp_path):
    """Operatör kaldırma adımından ÖNCEKİ ara hâl (drop-in kurulu, `.env-cp` hâlâ diskte ve BAYAT): konteynerin
    iki değişkeni de yan dosyadan gelir — bayat dosya hiçbir değeri ezemez."""
    _cp_dosyalari(tmp_path, eski=True, yan=True)
    ortam = _systemd_ortami(_etkin_env_dosyalari(), tmp_path)
    assert ortam == {"HINDSIGHT_CP_ACCESS_KEY": "SAHTE-KASA-ERISIM",
                     "HINDSIGHT_CP_DATAPLANE_API_KEY": "SAHTE-KASA-KIRACI"}


def test_A7_MODEL_yan_dosya_YOKSA_birim_ACILMAZ_eski_dosya_KURTARMAZ(tmp_path):
    """Tiresiz satırın anlamı: yan dosya yoksa birim açılmaz — eski `.env-cp` dursa bile ona DÜŞÜLMEZ (düşülseydi
    iki kanal sessizce geri gelirdi). Pozitif kontrol: 51 olmadan aynı sahne eski dosyayla AÇILIR."""
    _cp_dosyalari(tmp_path, eski=True, yan=False)
    assert _systemd_ortami(_etkin_env_dosyalari(), tmp_path) is None
    digerleri = [p for p in sorted(CP_DROPIN_DIZIN.glob("*.conf")) if p.name != DROPIN_51.name]
    assert _systemd_ortami(_etkin_env_dosyalari(digerleri), tmp_path) == {
        "HINDSIGHT_CP_ACCESS_KEY": "SAHTE-BAYAT-ERISIM", "HINDSIGHT_CP_DATAPLANE_API_KEY": "SAHTE-BAYAT-KIRACI"}


# =================================================================================================
# B) ARAÇLAR — anahtar `sudo -n cat <render hedefi>` borusundan
# =================================================================================================

SUDO_SIM = """#!/bin/sh
# sahte sudo — YALNIZ argümanları günlüğe yazar (değer argv'de olamaz; ölçülen de budur)
printf '%s\\n' "$*" >> "$SAHTE_SUDO_LOG"
if [ "${SAHTE_SUDO_KIP:-tamam}" = parola ]; then echo "sudo: a password is required" >&2; exit 1; fi
if [ "$#" = 3 ] && [ "$1" = "-n" ] && [ "$2" = "cat" ] && [ "$3" = "__KAYNAK__" ]; then
  exec cat "$SAHTE_SUDO_KAYNAK"
fi
echo "sahte sudo: beklenmeyen çağrı" >&2
exit 97
""".replace("__KAYNAK__", KAYNAK)

CAGRILAR = [
    pytest.param(SAYFA_OKU, (), id="sayfa_oku-liste"),
    pytest.param(SAYFA_OKU, ("meridian-hedef-sapma",), id="sayfa_oku-sayfa"),
    pytest.param(HAFIZA_SOR, (SORU,), id="hafiza_sor"),
]
BETIKLER = [pytest.param(SAYFA_OKU, (), id="sayfa_oku"), pytest.param(HAFIZA_SOR, (SORU,), id="hafiza_sor")]


def _sudo_ortami(tmp_path: pathlib.Path, port: int, *, icerik: bytes | None = None, kip: str = "tamam",
                 sudo_var: bool = True) -> tuple[dict, pathlib.Path]:
    """v547 ortamı + sahte sudo; `HAFIZA_ANAHTAR_DOSYASI` ÇIKARILIR (varsayılan kaynak = sudo borusu)."""
    ortam = _ortam(tmp_path, port)
    ortam.pop("HAFIZA_ANAHTAR_DOSYASI")
    binn = tmp_path / "sudo_bin"
    binn.mkdir()
    if sudo_var:
        (binn / "sudo").write_text(SUDO_SIM, encoding="utf-8")
        (binn / "sudo").chmod(0o755)
        yol = ortam["PATH"]
    else:
        # Sudo'suz PATH: yalnız python3'ün dizini (ve betiğin ihtiyaç duyduğu çekirdek araçların dizinleri
        # sudo içermediği ölçülür — içerirse sahne kurulamaz, test kendini atlar).
        yol = ":".join(p for p in ortam["PATH"].split(":") if not (pathlib.Path(p) / "sudo").exists())
    kaynak = tmp_path / "kok_kaynak"
    kaynak.write_bytes(icerik if icerik is not None else (SAHTE_ANAHTAR + "\n").encode())
    log = tmp_path / "sudo.log"
    ortam.update({"PATH": f"{binn}:{yol}", "SAHTE_SUDO_LOG": str(log), "SAHTE_SUDO_KAYNAK": str(kaynak),
                  "SAHTE_SUDO_KIP": kip})
    return ortam, log


def _sudo_cagrilari(log: pathlib.Path) -> list[str]:
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


@pytest.mark.parametrize("betik,argv", CAGRILAR)
def test_B1_VARSAYILAN_kaynak_SUDO_BORUSU_argvde_yalniz_YOL(sunucu, tmp_path, betik, argv):
    """Ezme yokken anahtar TEK bir `sudo -n cat <render hedefi>` çağrısının stdout'undan gelir; sunucu doğru
    Bearer'ı görür; sudo'nun argv'si YOLU taşır, DEĞERİ değil; istek anında hiçbir torunun argv'sinde anahtar yok."""
    ortam, log = _sudo_ortami(tmp_path, sunucu["port"])
    goruntuler: list[tuple[int, list[str], str]] = []
    sunucu["istek_kancasi"] = lambda: goruntuler.append(_torun_argvleri())
    r = _kos(betik, *argv, ortam=ortam)
    assert r.returncode == 0, r.stderr[-400:]
    assert sunucu["istekler"], "istek gitmedi"
    yetkiler_dogru = all(i[2] == "Bearer " + SAHTE_ANAHTAR for i in sunucu["istekler"])
    assert yetkiler_dogru, "sunucu beklenen Bearer başlığını görmedi"
    assert _sudo_cagrilari(log) == [f"-n cat {KAYNAK}"], _sudo_cagrilari(log)
    sudo_argvde = SAHTE_ANAHTAR in log.read_text(encoding="utf-8")
    assert not sudo_argvde, "anahtar sudo argv'sinde"
    assert goruntuler, "süreç tablosu ölçülemedi"
    for kod, argvler, hata in goruntuler:
        assert kod == 0, hata[-300:]
        sizan = [a[:120] for a in argvler if SAHTE_ANAHTAR in a]
        assert not sizan, f"anahtar bir torunun argv'sinde: {len(sizan)} süreç"
    cikti_sizdi = SAHTE_ANAHTAR in (r.stdout + r.stderr)
    assert not cikti_sizdi, "anahtar çıktıya düştü"


@pytest.mark.parametrize("kip", ["parola", "sudo_yok"])
@pytest.mark.parametrize("betik,argv", BETIKLER)
def test_B2_SUDO_DUSERSE_cikis_1_istek_ve_kayit_YOK(sunucu, tmp_path, betik, argv, kip):
    """`-n` parolasız sudo yoksa BEKLEMEDEN düşer (sahte: "a password is required", çıkış 1); sudo hiç yoksa
    `FileNotFoundError`. İkisinde de: çıkış 1, stdout boş, istek GİTMEZ, okuma kaydı YAZILMAZ, stderr tek
    satırda kaynağı adlandırır, traceback YOK (v552 E4'ün sudo ikizi)."""
    ortam, log = _sudo_ortami(tmp_path, sunucu["port"], kip="parola" if kip == "parola" else "tamam",
                              sudo_var=(kip == "parola"))
    if kip == "sudo_yok":
        sudo_gorunur = any((pathlib.Path(p) / "sudo").exists() for p in ortam["PATH"].split(":"))
        if sudo_gorunur:
            pytest.skip("PATH'ten sudo ayıklanamadı — sudo'suz sahne kurulamaz")
    r = _kos(betik, *argv, ortam=ortam)
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert r.stdout == ""
    assert sunucu["istekler"] == [], "anahtar okunamadığı hâlde istek gitti"
    assert not pathlib.Path(ortam["HAFIZA_OKUMA_KAYDI"]).exists(), "anahtarsız çağrı okuma kaydı yazdı"
    assert "HAFIZA ANAHTARI OKUNAMADI" in r.stderr and KAYNAK in r.stderr, r.stderr
    assert "Traceback" not in r.stderr, r.stderr
    assert r.stderr.count("\n") == 1, r.stderr
    if kip == "parola":
        assert "sudo" in r.stderr and _sudo_cagrilari(log) == [f"-n cat {KAYNAK}"]


@pytest.mark.parametrize("betik,argv", BETIKLER)
def test_B3_EZME_verilince_SUDO_CAGRILMAZ_dosya_duz_okunur(sunucu, tmp_path, betik, argv):
    """`HAFIZA_ANAHTAR_DOSYASI` arayüzü KORUNUR (test/yerel kullanım): verilirse o dosya düz okunur ve sudo
    HİÇ çağrılmaz (sahte sudo kaynağı YANLIŞ anahtarı taşır — çağrılsaydı sunucu 401 dönerdi)."""
    ortam, log = _sudo_ortami(tmp_path, sunucu["port"], icerik=b"YANLIS-ANAHTAR\n")
    dosya = tmp_path / "ezme.key"
    dosya.write_text(SAHTE_ANAHTAR + "\n", encoding="utf-8")
    ortam["HAFIZA_ANAHTAR_DOSYASI"] = str(dosya)
    r = _kos(betik, *argv, ortam=ortam)
    assert r.returncode == 0, r.stderr[-400:]
    assert _sudo_cagrilari(log) == [], "ezme varken sudo çağrıldı"
    assert all(i[2] == "Bearer " + SAHTE_ANAHTAR for i in sunucu["istekler"])


@pytest.mark.parametrize("icerik", [pytest.param(b"\r\n", id="crlf"), pytest.param(b"\n\n", id="coklu_lf"),
                                    pytest.param(b"", id="satir_sonu_yok")])
@pytest.mark.parametrize("betik,argv", BETIKLER)
def test_B4_SUDO_yolunda_da_YALNIZ_sondaki_CRLF_kirpilir(sunucu, tmp_path, betik, argv, icerik):
    """Kırpma sözleşmesi (v552 E5) kaynaktan bağımsızdır: boru da dosya gibi yalnız sondaki CR/LF'i kaybeder."""
    ortam, _ = _sudo_ortami(tmp_path, sunucu["port"], icerik=SAHTE_ANAHTAR.encode() + icerik)
    r = _kos(betik, *argv, ortam=ortam)
    assert r.returncode == 0, r.stderr[-400:]
    assert [i[2] for i in sunucu["istekler"]] == ["Bearer " + SAHTE_ANAHTAR] * len(sunucu["istekler"])


def test_B5_STATIK_eski_yol_YOK_sudo_cagrisi_SABIT_ve_iki_betikte_AYNI():
    """Gömülü Python'da `/opt/hindsight/.key` artık YOK; sudo çağrısı sabit liste (kabuk YOK — `shell=True`
    değer enjeksiyonuna ve kabuk argv'sine kapı açardı); anahtar bloğu iki betikte bayt-aynı (v552 E3b)."""
    bloklar = []
    for betik in (SAYFA_OKU, HAFIZA_SOR):
        _, _, py = _bolumler(betik)
        assert ESKI_KEY not in py, f"{betik.name}: eski düz kopya yolu gömülü Python'da"
        blok = py[py.index("# >>> anahtar"): py.index("# <<< anahtar")]
        assert f'KAYNAK = "{KAYNAK}"' in blok, betik.name
        assert '["sudo", "-n", "cat", KAYNAK]' in blok, betik.name
        assert "shell=True" not in blok, betik.name
        assert 'os.environ.get("HAFIZA_ANAHTAR_DOSYASI")' in blok, betik.name
        bloklar.append(blok)
    assert bloklar[0] == bloklar[1], "anahtar bloğu iki betikte AYRIŞTI"


# =================================================================================================
# C) ROTASYON + ENVANTER — ATOMİK
# =================================================================================================

def test_C1_KOPYA_TABLOSUNDA_emekli_yol_YOK_tenant_ve_cp_TEK_referans():
    k = v447._betik_kopyalari()
    assert not [x["yol"] for x in k if x["yol"] in EMEKLI_YOLLAR], "emekli yol kopya tablosunda"
    assert [(x["tur"], x["yol"]) for x in k if x["alt"] == "tenant"] == [("dosya", KAYNAK)]
    assert [(x["tur"], x["yol"]) for x in k if x["alt"] == "cp"] == [("dosya", KANON_CP)]


def test_C2_ENVANTER_emekli_listesi_UC_satir_TARIHLI_ve_kopyalardan_AYRIK():
    """Envanter girdileri SİLİNMEDİ, EMEKLİ edildi (dash-token üslubu: tarihli not) — ama `kopyalar` listesinde
    DEĞİL: orası `--kopyalar` ile BİREBİR eşittir (v447 A1/A2) ve emekli satır rotasyonun yazdığı bir kopya değil."""
    rk = _envanter()["rotasyon_kopyalari"]
    emekli = rk["emekli_kopyalar"]
    assert {(e["alt_komut"], e["sir"], e["tur"], e["yol"], e.get("alan")) for e in emekli} == BEKLENEN_EMEKLI
    for e in emekli:
        assert set(e) <= EMEKLI_SEMA, set(e) - EMEKLI_SEMA
        assert e["emekli"] == EMEKLI_TARIH, e
        assert len(str(e.get("not") or "")) >= 20, f"{e['yol']}: emeklilik notu yok/kısa"
    assert not [x["yol"] for x in rk["kopyalar"] if x["yol"] in EMEKLI_YOLLAR]


def test_C3_KASA_kopya_kaynaklarinda_emekli_yol_YOK():
    """`vault_sir_koy.sh` eşitlik kapısı kaldırılmış bir dosyayı "kopya OKUNAMADI" diye beklerdi (v491 A5 küme
    eşitliği de bu yüzden AYNI turda düşer)."""
    for g in _envanter()["vault_kv"]:
        for k in [g.get("kaynak"), *(g.get("kopya_kaynaklari") or [])]:
            if k:
                assert k["dosya"] not in EMEKLI_YOLLAR, f"{g['ad']}: emekli yol kaynak/kopya listesinde"


def _betik_emekli_yollari() -> list[str]:
    metin = BETIK.read_text(encoding="utf-8")
    m = re.search(r"^_emekli_kopyalar\(\) \{\n  cat <<'EMEKLI_SON'\n(.*?)\nEMEKLI_SON\n\}", metin, re.S | re.M)
    assert m, "betikte `_emekli_kopyalar` heredoc'u yok"
    return m.group(1).splitlines()


def test_C4_BETIGIN_emekli_listesi_ENVANTERLE_ayrismaz():
    """Kaçınılmaz kopya (betik PyYAML'sız `--envanter` koşar) + ayrışma çivisi (tek-kaynak yasası)."""
    yollar = _betik_emekli_yollari()
    assert len(yollar) == len(set(yollar)), yollar
    assert set(yollar) == {e["yol"] for e in _envanter()["rotasyon_kopyalari"]["emekli_kopyalar"]}


def test_C5_ENVANTER_emekli_kopya_VARKEN_BAGIRIR_deger_BASMAZ(tmp_path):
    """Bedel yasası: satır tablodan çıkınca `--envanter` `.key`i artık EŞİT/AYRI diye görmez — kayıp, emekli
    kopya denetimiyle karşılanır. Ara hâl (operatör adımı öncesi) iki dosya da duruyor."""
    kok, ortam = v447._sahte_ortam(tmp_path)
    (kok / ESKI_KEY.lstrip("/")).write_text(v447.ESKI["tenant"] + "\n", encoding="utf-8")
    (kok / ENV_CP.lstrip("/")).write_text("HINDSIGHT_CP_ACCESS_KEY=SAHTE-ERISIM-0590\n"
                                          f"HINDSIGHT_CP_DATAPLANE_API_KEY={v447.ESKI['tenant']}\n",
                                          encoding="utf-8")
    r = v447._kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stderr[-400:]
    for y in (ESKI_KEY, ENV_CP):
        assert f"  !! EMEKLİ KOPYA HÂLÂ VAR: {y}" in r.stdout, r.stdout
    # `.env-cp` taramada KALIR (d-1 emsali `.dash.env`): alanları artık hiçbir kopya satırının değil.
    assert f"BEYAN DIŞI KOPYA: {ENV_CP} [HINDSIGHT_CP_DATAPLANE_API_KEY]" in r.stdout, r.stdout
    assert f"BEYAN DIŞI KOPYA: {ENV_CP} [HINDSIGHT_CP_ACCESS_KEY]" in r.stdout, r.stdout
    sizdi = any(d in (r.stdout + r.stderr) for d in (v447.ESKI["tenant"], "SAHTE-ERISIM-0590"))
    assert not sizdi, "envanter DEĞER bastı"


def test_C6_ENVANTER_emekli_kopya_YOKKEN_YOK_der(tmp_path):
    """Kaldırma adımından sonraki hedef hâl — tohum (v447) bu hâldir."""
    kok, ortam = v447._sahte_ortam(tmp_path)
    for y in EMEKLI_YOLLAR:
        assert not (kok / y.lstrip("/")).exists(), f"tohum hedef hâlde değil: {y} var"
    r = v447._kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stderr[-400:]
    for y in (ESKI_KEY, ENV_CP):
        assert f"  emekli kopya: {y} → YOK" in r.stdout, r.stdout
    assert "EMEKLİ KOPYA HÂLÂ VAR" not in r.stdout


def test_C7_TENANT_eski_dosyalara_YAZMAZ(tmp_path):
    """`--tenant` (eski yol) artık yalnız render hedefini yazar: ara hâlde duran `.key`/`.env-cp` DOKUNULMADAN
    kalır (bayt bayt) — rotasyon emekli kopyayı "tazeleyip" yaşatmaz."""
    kok, ortam = v447._sahte_ortam(tmp_path)
    key, envcp = kok / ESKI_KEY.lstrip("/"), kok / ENV_CP.lstrip("/")
    key.write_text(v447.ESKI["tenant"] + "\n", encoding="utf-8")
    envcp.write_text(f"HINDSIGHT_CP_DATAPLANE_API_KEY={v447.ESKI['tenant']}\n", encoding="utf-8")
    once = (key.read_bytes(), envcp.read_bytes())
    r = v447._kos(BETIK, ortam, "--tenant")
    assert r.returncode == 0, r.stderr[-600:]
    assert (key.read_bytes(), envcp.read_bytes()) == once, "emekli dosyaya yazıldı"
    yeni = (kok / KAYNAK.lstrip("/")).read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"[0-9a-f]{64}", yeni), "render hedefi yeni değerle yazılmadı"


def test_C8_CP_KASA_YOLU_eski_kanal_YOK_der_env_cp_ye_YAZMAZ(tmp_path):
    """`--cp --vault` adım 6 (eski kanal) kopya tablosundan türer: env satırı yok → "YOK" der, `.env-cp`
    (ara hâlde duruyor) bayt bayt aynı kalır, CP yeni anahtarla açılır (değer yan dosyadan)."""
    kok, ortam, _, durum = v556._cp_ortami(tmp_path)
    envcp = kok / ENV_CP.lstrip("/")
    envcp.write_text("HINDSIGHT_CP_ACCESS_KEY=SAHTE-BAYAT-0590\n", encoding="utf-8")
    once = envcp.read_bytes()
    r = v447._kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 0, r.stderr[-600:]
    assert envcp.read_bytes() == once, "eski kanal dosyası yazıldı"
    assert "6/8 eski kanal: YOK" in r.stdout, r.stdout
    assert v556._etkin(kok) == v556._kasa(durum)[-1], "CP yeni anahtarla açılmadı"


def test_C9_DOSYALAR_blogu_ve_SPEC_env_cp_CIKTI_emekli_kayit_KALDIRMAYI_tasir():
    """`dosyalar:` "bugün hangi sır nerede yaşıyor"u söyler. 2026-09-29 sabahı `.env-cp` orada EMEKLİ hücresiyle
    duruyordu (dosya diskteydi, okuyucusu yoktu); 11:32Z'de A1'den KALDIRILDI → girdi ve spec §1 satırı AYNI turda
    çıktı (d-1 `.dash.env` emsali; v439 E0/E2/E3, v447 A5/S2/S3). Tarihçe SİLİNMEZ: `emekli_kopyalar` kayıtları
    kaldırma anını ve yedek dizinini (YOL — değer değil) taşır; kaldırılmış bir dosyanın kaydı bu iki alanı
    taşımıyorsa "nereye gitti, geri alma neyle yapılır" sorusunun cevabı yalnız bir oturum dökümünde kalırdı."""
    env = _envanter()
    assert ENV_CP not in {d["yol"] for d in env["dosyalar"]}, "kaldırılmış `.env-cp` hâlâ `dosyalar:` bloğunda"
    satir = [s for s in SPEC.read_text(encoding="utf-8").splitlines() if s.startswith(f"| `{ENV_CP}` |")]
    assert not satir, "kaldırılmış `.env-cp` spec §1 tablosunda duruyor"
    emekli = env["rotasyon_kopyalari"]["emekli_kopyalar"]
    kaldirilan = {e["yol"] for e in emekli if e.get("kaldirildi")}
    assert kaldirilan == set(EMEKLI_YOLLAR), f"kaldırma kaydı eksik/fazla: {sorted(kaldirilan)}"
    for e in emekli:
        if e["yol"] in EMEKLI_YOLLAR:
            assert e["kaldirildi"] == KALDIRMA_ANI, e["yol"]
            assert e.get("yedek_dizini") == YEDEK_DIZINI, e["yol"]
        # Genel kural (yeni emekli kayıtlar için de): biri varsa öteki de var — yedeksiz kaldırma kaydı yok.
        assert bool(e.get("kaldirildi")) == bool(e.get("yedek_dizini")), e["yol"]


def test_C10_VAULT_DONGUSU_tenant_TEK_KANAL_der(tmp_path):
    """Kapanan sırda "İKİ KANAL AÇIK" satırı YALAN olurdu — satır kopya tablosundan türer: render hedefi
    DIŞINDA kopyası kalmayan alt komut "TEK KANAL" der (kuru plan değil, gerçek döngünün son satırı)."""
    kod = subprocess.run(["bash", "-c", _fonksiyon("_kanal_beyani") + "\n" + _fonksiyon("_kopyalar")
                          + '\n_kanal_beyani "$1" "$2"\n', "_", "tenant", KAYNAK],
                         capture_output=True, text=True)
    assert kod.returncode == 0, kod.stderr
    assert kod.stdout.startswith(">> TEK KANAL"), kod.stdout
    kod2 = subprocess.run(["bash", "-c", _fonksiyon("_kanal_beyani") + "\n" + _fonksiyon("_kopyalar")
                           + '\n_kanal_beyani "$1" "$2"\n', "_", "kapi", "/etc/meridian/kapi_apikey"],
                          capture_output=True, text=True)
    assert kod2.stdout.startswith(">> İKİ KANAL AÇIK"), kod2.stdout


def _fonksiyon(ad: str) -> str:
    """Betikten tek fonksiyon gövdesi (`ad() {` … sütun-0 `}`)."""
    metin = BETIK.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(ad)}\(\) \{{\n.*?^\}}\n", metin, re.S | re.M)
    assert m, f"fonksiyon yok: {ad}"
    return m.group(0)


# =================================================================================================
# D) RUNBOOK — operatör adımı (yedek → kaldırma), dosyanın SONUNDA
# =================================================================================================

BASLIK = "## TSK-064 iki-kanal kapanışı"


#: Numaralı adımlar SIRAYLA ve her adımın TAŞIMASI gereken komut parçaları (brief: site.yml → restart →
#: doğrulama → yedek → kaldırma; kaldırma sonrası doğrulama). Konum ADIM BAŞLIĞINDAN ölçülür — tablo ya da giriş
#: metnindeki bir geçiş sırayı yanlış göstermesin.
ADIMLAR = [
    ("**0. Kod A1'de**", ["readlink -f ~/bin/hafiza_sor.sh"]),
    ("**1. A0 rolü**", ["site.yml --check --diff", "deploy/ansible/site.yml\n"]),
    ("**2. Restart**", ["sudo systemctl restart hindsight-cp"]),
    ("**3. Doğrulama — kaldırmadan ÖNCE**", ["systemctl show -p EnvironmentFiles hindsight-cp", "/api/auth/login",
                                             "~/bin/sayfa_oku.sh", "~/bin/hafiza_sor.sh"]),
    ("**4. Yedek**", ["/root/sir-yedek-", "-ikikanal", "install -m 0600 -o root -g root", "cmp -s"]),
    # 2026-09-29 11:32Z UYGULAMASI: `rm -f` DEĞİL — yedek dizininin `orijinal/` alt dizinine TAŞIMA (D3).
    ("**5. Kaldırma**", ['sudo test -d "$Y"', 'install -d -m 0700 -o root -g root "$Y/orijinal"',
                         f'mv {ESKI_KEY} {ENV_CP} "$Y/orijinal/"']),
    ("**6. Son doğrulama — kaldırmadan SONRA**", ["sudo systemctl restart hindsight-cp", "--envanter"]),
    ("**GERİ ALMA**", ["51-env-cp-kaldir.conf", "daemon-reload", "install -m 0600 -o ubuntu -g ubuntu"]),
]


def test_D1_RUNBOOK_SONUNDA_bolum_ve_ADIM_SIRASI():
    metin = RUNBOOK.read_text(encoding="utf-8")
    assert metin.count(BASLIK) == 1, "RUNBOOK'ta iki-kanal bölümü yok/çoğul"
    bolum = metin[metin.index(BASLIK):]
    assert not re.search(r"^## ", bolum[len(BASLIK):], re.M), "iki-kanal bölümü dosyanın SON bölümü değil"
    konumlar = [bolum.find(b) for b, _ in ADIMLAR]
    assert all(k >= 0 for k in konumlar) and all(bolum.count(b) == 1 for b, _ in ADIMLAR), \
        dict(zip([b for b, _ in ADIMLAR], konumlar))
    assert konumlar == sorted(konumlar), "adım SIRASI bozuk"
    for i, (baslik, parcalar) in enumerate(ADIMLAR):
        son = konumlar[i + 1] if i + 1 < len(konumlar) else len(bolum)
        govde = bolum[konumlar[i]:son]
        eksik = [p for p in parcalar if p not in govde]
        assert not eksik, f"{baslik}: eksik komut parçası {eksik}"


def test_D2_RUNBOOK_komutlari_DEGER_BASMAZ():
    """Doğrulama komutları sırrı TERMİNALE basmaz: anahtar yalnız borudan akar (`--data-binary @-`), hiçbir
    satır `cat <sır dosyası>`ı çıplak çalıştırmaz."""
    bolum = RUNBOOK.read_text(encoding="utf-8").split(BASLIK, 1)[1]
    ciplak = [s for s in bolum.splitlines()
              if re.search(r"\bcat\s+(/etc/meridian/hindsight_cp_access_key|/etc/hindsight/creds/\S+|"
                           r"/opt/hindsight/\.key|/opt/hindsight/\.env-cp\S*)\s*['\"]?\s*$", s)]
    assert not ciplak, ciplak
    assert "--data-binary @-" in bolum


def _adim_govdesi(baslik: str, sonraki: str) -> str:
    bolum = RUNBOOK.read_text(encoding="utf-8").split(BASLIK, 1)[1]
    return bolum[bolum.index(baslik):bolum.index(sonraki)]


def test_D3_KALDIRMA_UYGULANDI_notu_TASIMA_kalici_silme_YOK_ve_ENVANTERLE_ayrismaz():
    """Reçete gerçeği anlatır: 2026-09-29 11:32Z'de 5. adım `rm` ile DEĞİL, root-only yedek dizininin `orijinal/`
    alt dizinine TAŞIMAYLA uygulandı (kalıcı silme yok). (1) adımın komut bloklarında `rm` YOK; (2) UYGULANDI notu
    anı ve dizini söyler; (3) aynı iki gerçek envanterin emekli kayıtlarında da yaşar — ikisi AYRIŞMAZ
    (tek-kaynak yasası: kaçınılmaz kopya + ayrışma çivisi; dış çapa C9'daki sabitler)."""
    govde = _adim_govdesi("**5. Kaldırma**", "**6. Son doğrulama")
    kod = "\n".join(re.findall(r"```bash\n(.*?)```", govde, re.S))
    assert kod.strip(), "5. adımda komut bloğu yok"
    assert not re.search(r"\brm\b", kod), "5. adım hâlâ kalıcı silme (rm) reçetesi taşıyor"
    an = re.search(r"\*\*UYGULANDI (\d{4}-\d\d-\d\d \d\d:\d\dZ)\*\*", govde)
    dizin = re.search(r"`(/root/sir-yedek-\d{8}T\d{6}Z-ikikanal/)orijinal/`", govde)
    assert an and dizin, "5. adımda UYGULANDI notu (an + `<yedek>/orijinal/`) yok"
    assert (an.group(1), dizin.group(1)) == (KALDIRMA_ANI, YEDEK_DIZINI)
    kayit = {(e.get("kaldirildi"), e.get("yedek_dizini"))
             for e in _envanter()["rotasyon_kopyalari"]["emekli_kopyalar"] if e["yol"] in EMEKLI_YOLLAR}
    assert kayit == {(an.group(1), dizin.group(1))}, "RUNBOOK UYGULANDI notu envanterin kaldırma kaydıyla AYRIŞTI"

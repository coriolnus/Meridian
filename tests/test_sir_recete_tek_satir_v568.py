"""test_sir_recete_tek_satir_v568.py — TSK-237: geri alma reçetesinin "rollback düşerse" satırı operatörün A1'de
DOĞRUDAN koşacağı TEK SATIR komuttur — üç kasa dalında (genel döngü · `--db --vault` · `--cp --vault`) AYNI
yardımcıdan (2026-09-27).

NUMARA: `ls tests | grep _v568` boş (ana checkout + bütün worktree'ler tarandı 2026-09-27; en yüksek v567).

BULGU (TSK-064(b) raporu kaygı 4 + inceleme LOW-1). Üç dalın reçetesi rollback satırının altında yedek yolu
AÇIKLAMA olarak basıyordu: `düşerse ESKİ değer yedekte: <yedek> — STDIN'le: vault kv put <yol> value=-`. Yedek
0600 root'tur; operatör onu sudo ile okuyup boruya vermek ve kasa oturumunu (adres + yönetici jetonu) KENDİSİ
kurmak zorundaydı — reçete bunu söylemiyordu. Arıza anında yarım kalan reçete, sırrı elle taşıtır.

ROL-1 KARARI (brief): satır TEK bir yardımcıdan (`_geri_koy_satiri`) üretilen TEK SATIR komuttur; değer argv'ye
GİRMEZ (dosya → STDIN boru), yedek root 0600 kalır (okuma sudo ile), kasa ortamı betiğin KENDİ yöntemidir
(`VAULT_ADDR` · `$VAULT_BIN` · yönetici jetonu `login -no-print -` ile STDIN'den · oturum geçici HOME'da, çıkışta
silinir). db/cp'nin öteki çıktıları BİREBİR; iz kıyası değişen satırı BEYANLA bilir (E).

BÖLÜMLER
  A  sözleşme — tek kaynak (üç dal aynı yardımcı · kopya yok · eski biçim yok) · ortam betiğin kendisinden ·
     gövde disiplini · `bash -n`
  B  gerçek reçete — üç dalın beş evresinde satır basılır, YAZILDIĞI GİBİ koşulur, kasa yazım ÖNCESİ değere döner
  C  odaklı — sahte `sudo` (KİMLİK: aynı programı koşar, yalnız root'u işaretler) + sahte `vault` (STDIN'i kaydeden):
     değer STDIN'den, argv'de YOK (dinamik ps + çağrı kaydı), jeton STDIN'den, oturum geçici HOME'da ve silinir,
     root kimliğiyle · yedek yok/boş ya da login düşer → kasaya YAZIM YOK · CR/LF kırpılır
  E  iz kıyası — eski biçimli taban ile BİREBİR; tek fark BEYANLI satır (üç dal, dokuz senaryo)
  M  MUTASYONLAR — brief'in üçü (değer argv'ye · sudo kalkar · bir dalda eski biçim) + boş-yedek kapısı · trap ·
     login'in HOME yalıtımı

TEK KAYNAK (testte de): satırın biçimi, çözücüsü ve koşturucusu BURADA yaşar; v567 (TSK-064(b)) reçete iddialarını
buradan alır (v567 → v568; ters yön yok).

SIR DEĞERİ YOK: tohumlar `SAHTE-` önekli ve sahtedir. İddialar bool'a indirilir (`_iddia`); mesajlar yalnız ad,
etiket ya da maskeli metin taşır. Sahte `vault` STDIN'i kasa MODELİNE yazar (gerçek kasa gibi) ama çağrı kaydına
yalnız UZUNLUĞUNU yazar.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shlex
import stat
import subprocess
import sys

import pytest

from tests import test_cp_rotasyon_v556 as v556
from tests import test_sir_kasa_surum_v561 as v561
from tests import test_sir_uret_v557 as v557
from tests import test_vault_db_kasa_v538 as v538
from tests import test_vault_dalga1_baglama_v521 as v521
from tests.test_hindsight_anahtar_argv_v552 import _torunlar
from tests.test_sir_rotasyon_v447 import BETIK, DSN, ENVANTER, ESKI, _kos

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

YARDIMCI = "_geri_koy_satiri"
#: Reçete fonksiyonu → (yardımcı çağrısı sayısı = rollback satırı sayısı, ad, yol değişkeni).
RECETELER = {"_genel_kasa_recetesi": (1, "değer", "$yol"),
             "_db_kasa_recetesi": (2, "DSN", "$DB_KASA_YOL"),
             "_cp_kasa_recetesi": (2, "değer", "$CP_KASA_YOL")}
CAGRI_DESENI = re.compile(r'_geri_koy_satiri (değer|DSN) "(\$\w+)"')

#: Satırın biçimi — etiket + TEK SATIR komut. Etiket insan içindir; komut `): `dan sonrasıdır ve olduğu gibi koşulur.
ETIKET_DESENI = re.compile(r"^        düşerse \(TEK SATIR, root — yedekteki ESKİ (değer|DSN) STDIN'le kasaya; değer "
                           r"argv'ye GİRMEZ\): (.+)$")
KOMUT_DESENI = re.compile(r"^sudo bash -c '([^']*)' _ (.+)$")
YEDEK_ONEKI = "        düşerse ("
#: Eski biçim (9cf96240'a kadar üç dalda) — E'nin tabanı ve M3'ün mutasyonu bununla kurulur.
ESKI_SATIR_DESENI = re.compile(r"^        düşerse ESKİ (değer|DSN) yedekte: (\S+) — STDIN'le: vault kv put (\S+) value=-$")
ESKI_KOD = re.compile(r"düşerse ESKİ (değer|DSN) yedekte:")

#: Gövdenin STDIN borusu (betiğin kendi `_db_kasa_geri_al` yöntemi) — M1 bunu argv biçimine çevirir; v567 M2b de.
GOVDE_BORU = 'tr -d "\\r\\n" < "$4" | HOME="$h" "$2" kv put "$5" value=-'
GOVDE_ARGV = 'HOME="$h" "$2" kv put "$5" value="$(tr -d "\\r\\n" < "$4")"'
GOVDE_KAPI = 'test -s "$4" || { echo "yedek yok/boş: $4" >&2; exit 1; }; '
GOVDE_TRAP = 'trap "rm -rf \\"$h\\"" EXIT; '
GOVDE_LOGIN = 'HOME="$h" "$2" login -no-print - < "$3"'
BASARI = "kasa geri kondu: {yol}"

ISTEM = "SAHTE-ISTEM-0568"
ESKI_DEGER = "SAHTE-ESKI-DEGER-0568"
YENI_DEGER = "SAHTE-YENI-DEGER-0568"
JETON = "SAHTE-hvs-yonetici-0568"
ODAK_YOL = "secret/meridian/HINDSIGHT_API_TENANT_API_KEY"

_TOHUMLAR = v557._TOHUMLAR + (v561.ONCEKI_TENANT, v561.ONCEKI_NOUS, v561.LLM_V1, v561.LLM_V2, v561.YENI_NOUS,
                              v561.YENI_OR, v538.YENI_PG, v538.YENI_DSN, DSN, ISTEM, ESKI_DEGER, YENI_DEGER, JETON)
_ARIZA_BAYRAKLARI = ("SAHTE_RENDER", "SAHTE_PUT_IZIN", "SAHTE_ROLLBACK_KIRIK", "SAHTE_ALTER_DUSER")


def _adres_varsayilani() -> str:
    """Betiğin kendi `VAULT_ADDR` varsayılanı — beklenen değer UYDURULMAZ, betikten okunur."""
    m = re.search(r'^export VAULT_ADDR="\$\{VAULT_ADDR:-([^}"]+)\}"$', BETIK.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


ADRES = _adres_varsayilani()


# =================================================================================================
# YARDIMCILAR — satırın çözücüsü ve koşturucusu (v567 de bunları kullanır)
# =================================================================================================

_iddia = v557._iddia


def _maskeli(metin: str) -> str:
    for d in _TOHUMLAR:
        metin = metin.replace(d, "<SAHTE-TOHUM>")
    return re.sub(r"[A-Za-z0-9_+=-]{40,}", "<UZUN-JETON>", metin)


def _ozet(r: subprocess.CompletedProcess) -> str:
    return f"çıkış {r.returncode}\n--- stdout ---\n{_maskeli(r.stdout)}\n--- stderr ---\n{_maskeli(r.stderr)}"


def _yorumsuz(metin: str) -> str:
    return "\n".join(s for s in metin.splitlines() if not s.lstrip().startswith("#"))


def _yardimci_metni(betik: pathlib.Path = BETIK) -> str:
    try:
        return v521._fonksiyon(YARDIMCI, betik)
    except ValueError:
        return ""


def _coz(satir: str) -> dict | None:
    """Satır → {ne, komut, govde, args}. Etiket tutmazsa None. `komut` etiketten sonrasının TAMAMIdır (gevşek:
    mutantların komutu da koşulabilsin); `govde`/`args` yalnız `sudo bash -c '<gövde>' _ <5 argüman>` biçiminde dolar."""
    m = ETIKET_DESENI.match(satir)
    if not m:
        return None
    d = {"ne": m.group(1), "komut": m.group(2), "govde": None, "args": None}
    k = KOMUT_DESENI.match(m.group(2))
    if k:
        d["govde"] = k.group(1)
        try:
            d["args"] = shlex.split(k.group(2))
        except ValueError:
            d["args"] = None
    return d


def _yedek_ve_yol(satir: str) -> tuple[str, str] | None:
    """Satırın gösterdiği (yedek dosyası, kasa yolu) — biçim tutmazsa None."""
    d = _coz(satir)
    if not d or not d["args"] or len(d["args"]) != 5:
        return None
    return d["args"][3], d["args"][4]


def _stdin_govdesi(govde: str | None) -> bool:
    """Gövde değeri dosyadan STDIN'e BORULAR (betiğin yöntemi) ve `value=`e `-`den başka bir şey VERMEZ."""
    return bool(govde) and GOVDE_BORU in govde and not re.search(r"value=[^-]", govde)


def _yardimci_kos(betik: pathlib.Path, ne: str, yol: str, **degisken: str) -> subprocess.CompletedProcess:
    """Yardımcıyı betikten KESER ve yalıtılmış kabukta koşar (betiğin global değişkenleri ortamdan)."""
    kod = _yardimci_metni(betik) + f'\n{YARDIMCI} "$@"\n'
    return subprocess.run(["bash", "-c", kod, "_", ne, yol], capture_output=True, text=True,
                          env=dict(os.environ, **degisken))


def _kanon_govde() -> str:
    """Betiğin (BETIK) yardımcısının bastığı gövde — tek kaynak; örnek değerlerle üretilir."""
    r = _yardimci_kos(BETIK, "değer", "secret/x/y", VAULT_ADDR=ADRES, VAULT_BIN="/v", VAULT_JETON_DOSYASI="/j",
                      YEDEK="/y")
    d = _coz(r.stdout.rstrip("\n"))
    return (d or {}).get("govde") or ""


def _satiri_kos(komut: str, ortam: dict, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    """Operatörün yapıştıracağı komutu OLDUĞU GİBİ koşar (etkileşimli kabuğun yerine `bash -c`)."""
    return subprocess.run(["bash", "-c", komut], capture_output=True, text=True, env=ortam,
                          cwd=str(cwd) if cwd else None)


def _mod(p: pathlib.Path) -> int | None:
    return stat.S_IMODE(p.stat().st_mode) if p.exists() else None


def _ps_goruntuleri(dizin: pathlib.Path) -> list[list[str]]:
    """Her görüntüde YALNIZ bu pytest sürecinin torunlarının argv'si (v552/v556 deseni — başka worktree'deki
    koşumlar sahte kırmızı üretmesin)."""
    out = []
    for p in sorted(dizin.glob("ps_*.txt")):
        tablo = {}
        for satir in p.read_text(encoding="utf-8").splitlines():
            q = satir.split(None, 2)
            if len(q) >= 2:
                tablo[q[0]] = (q[1], q[2] if len(q) > 2 else "")
        out.append([tablo[pid][1] for pid in _torunlar(tablo)])
    return out


def _bicim_ihlalleri(metin: str, beklenen: list[tuple[str, str, str]], ortam: dict) -> list[str]:
    """Reçete metnindeki "düşerse" satırları: HEPSİ etiketli TEK SATIR · sayısı beklenen · her biri `sudo bash -c
    '<betiğin gövdesi>' _ <adres> <vault> <jeton> <yedek> <yol>` (ortam BETİĞİNKİ) · gövde STDIN borusu · `bash -n`
    temiz · eski biçim YOK. `beklenen`: (ad, yedek dosyası, yol)."""
    ih = []
    satirlar = [s for s in metin.splitlines() if s.startswith("        düşerse")]
    if any(ESKI_SATIR_DESENI.match(s) for s in satirlar):
        ih.append("eski biçim (açıklama) satırı VAR")
    cozulen = [_coz(s) for s in satirlar]
    if any(d is None for d in cozulen):
        ih.append("etiketsiz 'düşerse' satırı (TEK SATIR biçimi dışında)")
    cozulen = [d for d in cozulen if d]
    if len(cozulen) != len(beklenen):
        ih.append(f"TEK SATIR satırı {len(cozulen)} ({len(beklenen)} bekleniyordu)")
        return ih
    kanon = _kanon_govde()
    for d, (ne, yedek, yol) in zip(cozulen, beklenen):
        if d["govde"] is None or d["args"] is None:
            ih.append(f"{yol}: komut `sudo bash -c '<gövde>' _ <argümanlar>` biçiminde değil")
            continue
        if d["ne"] != ne:
            ih.append(f"{yol}: etiket '{d['ne']}' ('{ne}' bekleniyordu)")
        if d["args"] != [_adres(ortam), ortam["VAULT_BIN"], ortam["VAULT_TOKEN_FILE"], yedek, yol]:
            ih.append(f"{yol}: argümanlar betiğin kasa ortamı değil (adres · vault · jeton · yedek · yol)")
        if not _stdin_govdesi(d["govde"]):
            ih.append(f"{yol}: yedek yol satırı STDIN biçiminde değil")
        if d["govde"] != kanon:
            ih.append(f"{yol}: gövde yardımcının tek kaynağından farklı")
        for ad, kod in (("komut", d["komut"]), ("gövde", d["govde"])):
            if subprocess.run(["bash", "-n", "-c", kod], capture_output=True, text=True).returncode != 0:
                ih.append(f"{yol}: {ad} `bash -n` ile sözdizimi hatalı")
    return ih


def _adres(ortam: dict) -> str:
    return ortam.get("VAULT_ADDR") or ADRES


# =================================================================================================
# A) SÖZLEŞME
# =================================================================================================

def test_A0_ITHAL_EDILEN_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v556/v557/v561/v567 A0): ithal edilen modül başka ağaçtan yüklenirse çiviler BAŞKA betiği ölçer."""
    for yol in (BETIK, ENVANTER, pathlib.Path(v556.__file__), pathlib.Path(v557.__file__),
                pathlib.Path(v561.__file__), pathlib.Path(v538.__file__), pathlib.Path(v521.__file__)):
        _iddia(yol.resolve().is_relative_to(KOK_DEPO.resolve()), f"yabancı ağaçtan ithal: {yol}")


def _a1_ihlalleri(betik: pathlib.Path = BETIK) -> list[str]:
    """Tek-kaynak yasası (ayrışma çivisi): yardımcı TAM bir kez tanımlı; üç reçete onu rollback satırı kadar çağırır
    (genel 1 · db 2 · cp 2), doğru ad ve KENDİ yol değişkeniyle; etiket metni yalnız yardımcıda; eski biçim hiçbir kod
    satırında yok; yardımcıyı reçeteler DIŞINDA kimse çağırmaz."""
    metin = betik.read_text(encoding="utf-8")
    ih = []
    if metin.count(f"\n{YARDIMCI}() {{\n") != 1:
        return [f"{YARDIMCI} TAM bir kez tanımlı değil ({metin.count(f'{chr(10)}{YARDIMCI}() {{{chr(10)}')})"]
    toplam = 0
    for fn, (adet, ne, degisken) in RECETELER.items():
        govde = _yorumsuz(v521._fonksiyon(fn, betik))
        cagri = CAGRI_DESENI.findall(govde)
        rollback = govde.count("vault kv rollback -version=$")
        toplam += len(cagri)
        if len(cagri) != adet or rollback != adet:
            ih.append(f"{fn}: yardımcı çağrısı {len(cagri)} · rollback satırı {rollback} ({adet}/{adet} bekleniyordu)")
        if any(c != (ne, degisken) for c in cagri):
            ih.append(f"{fn}: çağrı ('{ne}', {degisken}) değil: {sorted(set(cagri))}")
    kod = _yorumsuz(metin)
    if len(CAGRI_DESENI.findall(kod)) != toplam:
        ih.append("yardımcı reçeteler DIŞINDA da çağrılıyor")
    if kod.count("düşerse (TEK SATIR") != 1 or "düşerse (TEK SATIR" not in _yardimci_metni(betik):
        ih.append("etiket metni yardımcı DIŞINDA da var (kopya) ya da yardımcıda yok")
    if ESKI_KOD.search(kod):
        ih.append("eski biçim (açıklama) satırı kodda duruyor")
    return ih


def test_A1_TEK_KAYNAK_uc_recete_AYNI_yardimci_rollback_kadar_KOPYA_ve_ESKI_bicim_YOK():
    ih = _a1_ihlalleri()
    _iddia(not ih, "\n".join(ih))


def _a2_ihlalleri(betik: pathlib.Path = BETIK) -> list[str]:
    """Kasa ortamı BETİĞİN KENDİSİNDEN (uydurma yok): yardımcı `$VAULT_ADDR` · `$VAULT_BIN` · `$VAULT_JETON_DOSYASI`
    · `$YEDEK/vault/<yol>` · `<yol>` basar — `_vault`un ikilisi, `_vault_oturum`un jeton dosyası ve login biçimi, global
    `export VAULT_ADDR`. Gövde disiplini: `set -euo pipefail` · boş/eksik yedekte YAZIMDAN ÖNCE durur · her kasa
    çağrısı geçici HOME'da (`_vault`un `HOME="$ISLIK"` ikizi) ve trap onu siler · değer dosyadan STDIN'e borulanır
    (betiğin `tr -d` + `value=-` yöntemi) · `VAULT_TOKEN`/`$(cat`/tek tırnak YOK."""
    ih = []
    yardimci = _yorumsuz(_yardimci_metni(betik))
    if '"$VAULT_ADDR" "$VAULT_BIN" "$VAULT_JETON_DOSYASI" "$YEDEK/vault/$2" "$2"' not in yardimci:
        ih.append("yardımcı betiğin kasa değişkenlerini (VAULT_ADDR · VAULT_BIN · VAULT_JETON_DOSYASI · YEDEK) basmıyor")
    if "sudo bash -c '%s' _ %q %q %q %q %q" not in yardimci:
        ih.append("yardımcının komut kalıbı `sudo bash -c '<gövde>' _ %q×5` değil")
    metin = betik.read_text(encoding="utf-8")
    # `_vault` TEK satırlık fonksiyondur (`_fonksiyon` çok satırlı gövde keser) — satırın kendisi okunur.
    if not re.search(r'^_vault\(\) \{ HOME="\$ISLIK" "\$VAULT_BIN" "\$@"; \}$', metin, re.M) \
            or not re.search(r"^export VAULT_ADDR=", metin, re.M):
        ih.append("betiğin kendi kasa çağrısı (_vault: HOME yalıtımı + VAULT_BIN · VAULT_ADDR) değişti — yardımcı "
                  "yeniden türetilmeli")
    oturum = v521._fonksiyon("_vault_oturum", betik)
    if 'login -no-print - < "$VAULT_JETON_DOSYASI"' not in oturum:
        ih.append("_vault_oturum jetonu `login -no-print -` ile STDIN'den almıyor — yardımcı yeniden türetilmeli")
    r = _yardimci_kos(betik, "değer", "secret/x/y", VAULT_ADDR=ADRES, VAULT_BIN="/v", VAULT_JETON_DOSYASI="/j",
                      YEDEK="/y")
    d = _coz(r.stdout.rstrip("\n"))
    govde = (d or {}).get("govde") or ""
    if not govde:
        return ih + ["yardımcı `sudo bash -c '<gövde>'` biçiminde bir satır basmadı"]
    if not govde.startswith("set -euo pipefail; "):
        ih.append("gövde `set -euo pipefail` ile başlamıyor")
    if GOVDE_KAPI not in govde or govde.find(GOVDE_KAPI) > govde.find("kv put"):
        ih.append("boş/eksik yedek kapısı yok ya da yazımdan SONRA")
    if govde.count('HOME="$h" "$2" ') != 2 or GOVDE_LOGIN not in govde:
        ih.append("kasa çağrıları geçici HOME'da değil ya da jeton `login -no-print -` ile STDIN'den alınmıyor")
    if GOVDE_TRAP not in govde or 'mktemp -d "${TMPDIR:-/tmp}/sir-geri.XXXXXXXX"' not in govde:
        ih.append("geçici HOME (mktemp, adlı şablon) ya da onu silen trap yok")
    if not _stdin_govdesi(govde) or "tr -d '\\r\\n' < " not in v521._fonksiyon("_db_kasa_geri_al", betik):
        ih.append("değer dosyadan STDIN'e borulanmıyor (betiğin `tr -d` + `value=-` yöntemi)")
    if "VAULT_TOKEN" in govde or "$(cat" in govde or "'" in govde:
        ih.append("gövdede VAULT_TOKEN / $(cat / tek tırnak var")
    if 'export VAULT_ADDR="$1"' not in govde:
        ih.append("gövde VAULT_ADDR'ı betiğin değerinden (1. argüman) kurmuyor")
    return ih


def test_A2_ORTAM_betigin_KENDI_kasa_cagrisindan_GOVDE_disiplini():
    ih = _a2_ihlalleri()
    _iddia(not ih, "\n".join(ih))


def test_A3_SOZDIZIMI_satir_ve_govde_bash_n_TEMIZ_etiket_TEK_satir():
    """Yardımcının örnek değerlerle bastığı satır TEK satırdır, etiket deseni tutar; komut ve gövde `bash -n` temiz."""
    r = _yardimci_kos(BETIK, "DSN", "secret/meridian/HINDSIGHT_API_DATABASE_URL", VAULT_ADDR=ADRES,
                      VAULT_BIN="/usr/local/bin/vault", VAULT_JETON_DOSYASI="/etc/vault/admin.token",
                      YEDEK="/root/sir-yedek-20260927T041500Z-db")
    _iddia(r.returncode == 0 and r.stdout.count("\n") == 1, "yardımcı TEK satır basmadı\n" + _ozet(r))
    d = _coz(r.stdout.rstrip("\n"))
    _iddia(d is not None and d["ne"] == "DSN" and d["govde"] and d["args"] == [
        ADRES, "/usr/local/bin/vault", "/etc/vault/admin.token",
        "/root/sir-yedek-20260927T041500Z-db/vault/secret/meridian/HINDSIGHT_API_DATABASE_URL",
        "secret/meridian/HINDSIGHT_API_DATABASE_URL"], "satır biçimi tutmadı\n" + _maskeli(r.stdout))
    for ad, kod in (("komut", d["komut"]), ("gövde", d["govde"])):
        n = subprocess.run(["bash", "-n", "-c", kod], capture_output=True, text=True)
        _iddia(n.returncode == 0, f"{ad} `bash -n` hatalı: {n.stderr}")


# =================================================================================================
# B) GERÇEK REÇETE — üç dal, beş evre: satır YAZILDIĞI GİBİ koşulur
# =================================================================================================

#: dal → (dünya kurucu, argv, girdi, kasa okuyucu, alt komut, ad, kasa yolu, yazım ÖNCESİ değer)
DAL = {
    "genel": (v561._dunya, ("--tenant", "--vault"), f"{ISTEM}\n", lambda d: v561._kasa(d, v561.TENANT_YOLU),
              "tenant", "değer", v561.TENANT_YOLU, ESKI["tenant"]),
    "db": (v561._dunya_db, ("--db", "--vault"), f"{v538.YENI_PG}\n", v538._kasa, "db", "DSN", v538.DB_KASA, DSN),
    "cp": (v561._dunya_cp, ("--cp", "--vault"), "", v556._kasa, "cp", "değer", v556.KASA_YOLU, v556.ESKI_CP),
}
B_SENARYO = (("genel_kasa", "genel", {"SAHTE_RENDER": "yok"}, 2),
             ("db_kasa", "db", {"SAHTE_ALTER_DUSER": "1", "SAHTE_ROLLBACK_KIRIK": "1", "SAHTE_PUT_IZIN": "1"}, 1),
             ("db_alter", "db", {}, 0),
             ("cp_kasa", "cp", {"SAHTE_RENDER": "yok"}, 2),
             ("cp_yayim", "cp", {}, 0))


def _b_ihlalleri(tmp_path: pathlib.Path, dal: str, bayrak: dict, rc: int, betik: pathlib.Path = BETIK) -> list[str]:
    """Betik koşar → reçetede TEK "düşerse" satırı, betiğin ortamıyla · kasa YENİ değerde · satırın komutu OLDUĞU GİBİ
    (arıza bayrakları kalkmış ortamda) koşulur → çıkış 0 · sudo'dan geçti · kasa yazım ÖNCESİ değere döndü · yedek
    dosyası değişmedi ve 0600 · geçici HOME kalmadı · değer hiçbir yüzeyde/argv'de yok."""
    dunya, argv, girdi, kasa, alt, ne, yol, eski = DAL[dal]
    kok, ortam, log, durum = dunya(tmp_path, **bayrak)
    r = _kos(betik, ortam, *argv, girdi=girdi)
    ih = [] if r.returncode == rc else [f"betik çıkışı {r.returncode} ({rc} bekleniyordu)"]
    yedekler = sorted((kok / "root").glob(f"sir-yedek-*-{alt}"))
    if len(yedekler) != 1:
        return ih + [f"tam bir '{alt}' yedek dizini yok"]
    yedek = yedekler[0] / "vault" / yol
    ih += _bicim_ihlalleri("\n".join(v561._recete(r.stderr)), [(ne, str(yedek), yol)], ortam)
    yeni = kasa(durum)[-1]
    if yeni == eski:
        ih.append("sahne kurulamadı: kasa zaten yazım ÖNCESİ değerde")
    ds = [d for d in (_coz(s) for s in v561._recete(r.stderr)) if d]
    if len(ds) != 1:
        return ih + ["koşulacak TEK SATIR yok"]
    once = yedek.read_bytes() if yedek.is_file() else None
    argv_once = (kok / ".sahte" / "argv.log").read_text(encoding="utf-8")
    kos = {k: v for k, v in ortam.items() if k not in _ARIZA_BAYRAKLARI}
    y = _satiri_kos(ds[0]["komut"], kos, cwd=tmp_path)
    if y.returncode != 0 or BASARI.format(yol=yol) not in y.stdout:
        ih.append(f"satır koşmadı: çıkış {y.returncode}")
    yeni_argv = (kok / ".sahte" / "argv.log").read_text(encoding="utf-8")[len(argv_once):]
    if not any(s.startswith("sudo bash -c ") for s in yeni_argv.splitlines()):
        ih.append("satır sudo'dan geçmedi (argv kaydında `sudo bash -c` yok)")
    if kasa(durum)[-1] != eski:
        ih.append("satır koşulunca kasa yazım ÖNCESİ değere DÖNMEDİ")
    if once is None or yedek.read_bytes() != once or _mod(yedek) != 0o600:
        ih.append("yedek dosyası yok, değişti ya da 0600 değil")
    if list(pathlib.Path(ortam["TMPDIR"]).glob("sir-geri.*")):
        ih.append("geçici HOME (sir-geri.*) silinmedi")
    ih += v557._sizinti(y, kok, log, eski, yeni)
    return ih


@pytest.mark.parametrize("etiket,dal,bayrak,rc", B_SENARYO, ids=[b[0] for b in B_SENARYO])
def test_B1_GERCEK_RECETE_satir_YAZILDIGI_GIBI_kosulur_kasa_yazim_ONCESI_degere_doner(tmp_path, etiket, dal, bayrak, rc):
    ih = _b_ihlalleri(tmp_path, dal, bayrak, rc)
    _iddia(not ih, _maskeli(f"{etiket}:\n" + "\n".join(ih)))


# =================================================================================================
# C) ODAKLI — sahte sudo (KİMLİK) + sahte vault (STDIN'i kaydeden)
# =================================================================================================

SIM_SUDO_ODAK = '''#!__PY__
"""Sahte sudo = KİMLİK: çocuğu AYNI programla koşar; yalnız `SAHTE_UID=0` verir (root'u işaretler) ve argv'sini
kaydeder."""
import json, os, sys
with open(os.path.join(os.environ["V568_KOK"], "kayit.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"arac": "sudo", "argv": sys.argv[1:]}) + "\\n")
os.execvpe(sys.argv[1], sys.argv[1:], dict(os.environ, SAHTE_UID="0"))
'''

SIM_VAULT_ODAK = '''#!__PY__
"""Sahte vault — STDIN'i KASA MODELİNE kaydeder; çağrı kaydına argv, HOME, VAULT_ADDR, kimlik ve STDIN'in yalnız
UZUNLUĞU yazılır; her çağrıda süreç tablosu görüntüsü. `login -no-print -`: STDIN jetonu `$HOME/.vault-token`a (0600)
— gerçek jeton yardımcısı. `kv put <yol> value=-`: `$HOME/.vault-token` yönetici jetonu değilse YETKİSİZ (2).
`SAHTE_LOGIN_KIRIK=1` → login düşer."""
import json, os, subprocess, sys
KOK = os.environ["V568_KOK"]
a = sys.argv[1:]
girdi = sys.stdin.read() if a[-1:] in (["-"], ["value=-"]) else ""
ps = subprocess.run(["ps", "-A", "-ww", "-o", "pid=,ppid=,args="], capture_output=True, text=True).stdout
psd = os.path.join(KOK, "ps")
with open(os.path.join(psd, "ps_%04d.txt" % len(os.listdir(psd))), "w", encoding="utf-8") as fh:
    fh.write(ps)
home = os.environ.get("HOME", "")
oturum = os.path.join(home, ".vault-token")
with open(os.path.join(KOK, "kayit.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"arac": "vault", "argv": a, "home": home, "adres": os.environ.get("VAULT_ADDR"),
                         "uid": os.environ.get("SAHTE_UID"), "oturum": os.path.exists(oturum),
                         "girdi_boy": len(girdi)}) + "\\n")
if a == ["login", "-no-print", "-"]:
    if os.environ.get("SAHTE_LOGIN_KIRIK") == "1":
        sys.stderr.write("Error authenticating: permission denied\\n")
        sys.exit(2)
    fd = os.open(oturum, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, girdi.strip().encode())
    os.close(fd)
    sys.exit(0)
if a[:2] == ["kv", "put"] and len(a) == 4 and a[3] == "value=-":
    with open(os.path.join(KOK, "etc", "vault", "admin.token"), encoding="utf-8") as fh:
        jeton = fh.read().strip()
    if not os.path.exists(oturum) or open(oturum, encoding="utf-8").read() != jeton:
        sys.stderr.write("Error writing data to %s: permission denied\\n" % a[2])
        sys.exit(2)
    kasa = os.path.join(KOK, "kasa.json")
    with open(kasa, encoding="utf-8") as fh:
        d = json.load(fh)
    d.setdefault(a[2], []).append(girdi)
    with open(kasa, "w", encoding="utf-8") as fh:
        json.dump(d, fh)
    print("Key Value / version %d" % len(d[a[2]]))
    sys.exit(0)
sys.stderr.write("sim vault: tanınmayan çağrı\\n")
sys.exit(2)
'''


def _odak(tmp_path: pathlib.Path, betik: pathlib.Path = BETIK, yedek_icerik: str | None = ESKI_DEGER + "\n",
          **bayrak: str):
    """A1'in küçük modeli: yönetici jetonu (0400) · yedek (0700 dizinler, 0600 dosya) · kasa YENİ değerde · operatör
    kabuğu ubuntu (`SAHTE_UID=1000`, HOME `ev/`). Satır BETİĞİN yardımcısından (ya da mutantınkinden) üretilir."""
    kok = tmp_path / "odak"
    for d in ("bin", "ev", "tmp", "ps", "etc/vault"):
        (kok / d).mkdir(parents=True)
    jeton = kok / "etc/vault/admin.token"
    jeton.write_text(JETON + "\n", encoding="utf-8")
    jeton.chmod(0o400)
    yedek_dizini = kok / "root" / "sir-yedek-20260927T041500Z-tenant"
    yedek = yedek_dizini / "vault" / ODAK_YOL
    yedek.parent.mkdir(parents=True)
    for p in (yedek_dizini, yedek_dizini / "vault", yedek.parent.parent, yedek.parent):
        p.chmod(0o700)
    if yedek_icerik is not None:
        yedek.write_text(yedek_icerik, encoding="utf-8")
        yedek.chmod(0o600)
    (kok / "kasa.json").write_text(json.dumps({ODAK_YOL: [ESKI_DEGER, YENI_DEGER]}), encoding="utf-8")
    (kok / "kayit.jsonl").write_text("", encoding="utf-8")
    for ad, govde in (("sudo", SIM_SUDO_ODAK), ("vault", SIM_VAULT_ODAK)):
        (kok / "bin" / ad).write_text(govde.replace("__PY__", sys.executable), encoding="utf-8")
        (kok / "bin" / ad).chmod(0o755)
    ortam = dict(os.environ, PATH=f"{kok / 'bin'}:{os.environ['PATH']}", HOME=str(kok / "ev"),
                 TMPDIR=str(kok / "tmp"), SAHTE_UID="1000", V568_KOK=str(kok))
    for b in ("VAULT_ADDR", "VAULT_TOKEN", "SAHTE_LOGIN_KIRIK"):
        ortam.pop(b, None)
    ortam.update(bayrak)
    y = _yardimci_kos(betik, "değer", ODAK_YOL, VAULT_ADDR=ADRES, VAULT_BIN=str(kok / "bin" / "vault"),
                      VAULT_JETON_DOSYASI=str(jeton), YEDEK=str(yedek_dizini))
    return kok, ortam, y.stdout.rstrip("\n"), yedek


def _kayitlar(kok: pathlib.Path) -> list[dict]:
    return [json.loads(s) for s in (kok / "kayit.jsonl").read_text(encoding="utf-8").splitlines() if s]


def _kasa_odak(kok: pathlib.Path) -> list[str]:
    return json.loads((kok / "kasa.json").read_text(encoding="utf-8"))[ODAK_YOL]


def _odak_kos(tmp_path: pathlib.Path, betik: pathlib.Path = BETIK, yedek_icerik: str | None = ESKI_DEGER + "\n",
              **bayrak: str):
    kok, ortam, satir, yedek = _odak(tmp_path, betik, yedek_icerik, **bayrak)
    d = _coz(satir)
    once = yedek.read_bytes() if yedek.is_file() else None
    r = _satiri_kos(d["komut"], ortam, cwd=kok) if d else None
    return kok, r, satir, yedek, once


def _argv_ihlalleri(kok: pathlib.Path, yedek: pathlib.Path) -> list[str]:
    """Dinamik: sahte vault'un her çağrısındaki süreç tablosu (bu pytest'in torunları) + çağrı kaydının argv'leri.
    Pozitif kontrol: görüntüler `kv put <yol> value=-`yi ve yedeği taşıyan `bash -c`yi GÖRÜYOR. Negatif: ESKİ/YENİ
    değer ve yönetici jetonu (ve sha256'larının ilk 8 hanesi) hiçbir argv'de yok. Mesaj değeri basmaz."""
    ps = [a for g in _ps_goruntuleri(kok / "ps") for a in g]
    ih = []
    if not ps:
        return ["süreç tablosu görüntüsü YOK — ölçülemedi"]
    if not any(f"kv put {ODAK_YOL} value=-" in a for a in ps):
        ih.append("POZİTİF KONTROL: ps `kv put <yol> value=-` argv'sini görmedi")
    if not any("bash -c" in a and str(yedek) in a for a in ps):
        ih.append("POZİTİF KONTROL: ps yedeği taşıyan `bash -c` argv'sini görmedi")
    argvler = ps + [" ".join(k["argv"]) for k in _kayitlar(kok)]
    for i, d in enumerate((ESKI_DEGER, YENI_DEGER, JETON)):
        h8 = hashlib.sha256(d.encode()).hexdigest()[:8]
        if any(d in a for a in argvler):
            ih.append(f"değer #{i} argv'de")
        if any(h8 in a for a in argvler):
            ih.append(f"değer #{i} HASH'i argv'de")
    return ih


def _odak_ihlalleri(kok: pathlib.Path, r: subprocess.CompletedProcess | None, yedek: pathlib.Path,
                    once: bytes | None) -> list[str]:
    """Başarı sözleşmesi — C1 ve mutasyon çivileri AYNI liste."""
    if r is None:
        return ["satır etiketli TEK SATIR değil — koşulamadı"]
    ih = [] if r.returncode == 0 else [f"çıkış {r.returncode} (0 bekleniyordu)"]
    k = _kayitlar(kok)
    vault = [x for x in k if x["arac"] == "vault"]
    sudo = [x for x in k if x["arac"] == "sudo"]
    if [x["argv"][:2] for x in vault] != [["login", "-no-print"], ["kv", "put"]] or \
            vault[0]["argv"] != ["login", "-no-print", "-"] or vault[1]["argv"] != ["kv", "put", ODAK_YOL, "value=-"]:
        ih.append("kasa çağrıları `login -no-print -` → `kv put <yol> value=-` değil")
    if len(sudo) != 1 or sudo[0]["argv"][:2] != ["bash", "-c"]:
        ih.append(f"satır sudo'dan TAM bir kez geçmedi ({len(sudo)})")
    if not vault or any(x["uid"] != "0" for x in vault):
        ih.append("kasa çağrıları root kimliğiyle koşmadı (sudo yok)")
    evler = {x["home"] for x in vault}
    gecici = kok / "tmp"
    if len(evler) != 1 or not all(pathlib.Path(e).parent == gecici and pathlib.Path(e).name.startswith("sir-geri.")
                                  for e in evler):
        ih.append("oturum login ve put'ta AYNI geçici HOME'da değil (sir-geri.*)")
    if any(pathlib.Path(e).exists() for e in evler) or list(gecici.glob("sir-geri.*")):
        ih.append("geçici HOME silinmedi — yönetici oturumu diskte kaldı")
    if (kok / "ev" / ".vault-token").exists():
        ih.append("yönetici oturumu kullanıcının HOME'una düştü")
    if any(x["adres"] != ADRES for x in vault):
        ih.append("VAULT_ADDR betiğin adresi değil")
    put = [x for x in vault if x["argv"][:2] == ["kv", "put"]]
    if put and not put[0]["oturum"]:
        ih.append("put anında oturum yok (jeton STDIN'den login edilmedi)")
    kasa = _kasa_odak(kok)
    if len(kasa) != 3 or kasa[-1] != ESKI_DEGER:
        ih.append("kasa yedekteki ESKİ değere dönmedi (değer STDIN'den gelmedi ya da kırpılmadı)")
    if once is None or yedek.read_bytes() != once or _mod(yedek) != 0o600:
        ih.append("yedek dosyası değişti ya da 0600 değil")
    if BASARI.format(yol=ODAK_YOL) not in r.stdout:
        ih.append("başarı satırı yok")
    return ih + _argv_ihlalleri(kok, yedek)


def test_C1_ODAK_deger_STDINden_argvde_YOK_jeton_STDINden_gecici_HOME_silinir_root(tmp_path):
    """Brief'in çekirdeği: satır sahte kasa ortamında GERÇEKTEN koşulur. Yedekteki değer kasaya STDIN'den gider
    (kasa modeli), argv'de YOK (dinamik ps + çağrı kaydı); jeton `login -no-print -` ile STDIN'den; oturum geçici
    HOME'da, put onu görür, çıkışta silinir, kullanıcının HOME'una düşmez; iki kasa çağrısı da root kimliğiyle."""
    kok, r, satir, yedek, once = _odak_kos(tmp_path)
    ih = _odak_ihlalleri(kok, r, yedek, once)
    _iddia(not ih, "\n".join(ih) + ("\n" + _ozet(r) if r else "\n" + _maskeli(satir)))


def _yazim_yok_ihlalleri(kok: pathlib.Path, r: subprocess.CompletedProcess | None, metin: str | None) -> list[str]:
    if r is None:
        return ["satır koşulamadı"]
    ih = [] if r.returncode != 0 else ["çıkış 0 (düşmeliydi)"]
    if any(x["arac"] == "vault" and x["argv"][:2] == ["kv", "put"] for x in _kayitlar(kok)):
        ih.append("kasaya YAZIM denendi")
    if _kasa_odak(kok) != [ESKI_DEGER, YENI_DEGER]:
        ih.append("kasa değişti")
    if list((kok / "tmp").glob("sir-geri.*")) or (kok / "ev" / ".vault-token").exists():
        ih.append("geçici HOME ya da oturum kaldı")
    if metin and metin not in r.stderr:
        ih.append(f"açık hata satırı yok ({metin})")
    return ih


@pytest.mark.parametrize("kip", ["yok", "bos"])
def test_C2_YEDEK_yok_ya_da_BOS_ise_DURUR_kasaya_BOS_deger_YAZILMAZ(tmp_path, kip):
    """Boru eksik/boş dosyada `tr`ı düşürür ama `kv put` boş STDIN'i yine okur ve kasaya BOŞ değer yazar (pipefail
    yalnız çıkış kodunu düzeltir, yazımı geri almaz). Kapı YAZIMDAN ÖNCE durdurur."""
    kok, r, _, _, _ = _odak_kos(tmp_path, yedek_icerik=None if kip == "yok" else "")
    ih = _yazim_yok_ihlalleri(kok, r, "yedek yok/boş")
    _iddia(not ih, "\n".join(ih) + ("\n" + _ozet(r) if r else ""))


def test_C3_LOGIN_duserse_YAZIM_YOK_gecici_HOME_silinir(tmp_path):
    kok, r, _, _, _ = _odak_kos(tmp_path, SAHTE_LOGIN_KIRIK="1")
    ih = _yazim_yok_ihlalleri(kok, r, None)
    _iddia(not ih, "\n".join(ih) + ("\n" + _ozet(r) if r else ""))


def test_C4_CRLF_kirpilir_kasaya_ciplak_deger_gider(tmp_path):
    """Betiğin kendi yöntemi (`tr -d '\\r\\n'`): Windows satır sonlu bir yedek bile kasaya çıplak değeri koyar."""
    kok, r, _, yedek, once = _odak_kos(tmp_path, yedek_icerik=ESKI_DEGER + "\r\n")
    ih = _odak_ihlalleri(kok, r, yedek, once)
    _iddia(not ih, "\n".join(ih) + ("\n" + _ozet(r) if r else ""))


# =================================================================================================
# E) İZ KIYASI — eski biçimli taban ile BİREBİR; tek fark BEYANLI satır
# =================================================================================================
# BEYANLI FARK: iz kıyasının bildiği TEK değişiklik reçetenin "rollback düşerse" satırıdır (eski: açıklama; yeni: TEK
# SATIR komut). İki biçim de `<GERİ-KOY ad yedek yol>` jetonuna iner; başka HER satır — çıkış · stdout · stderr ·
# kasa/Agent olay sırası · kasa argv'si · dosya durumları — BİREBİR. Taban: bugünkü betikte yardımcı çağrıları 9cf96240'ın
# satır içi açıklamasına geri çevrilir (çapa sayıları pinli).

ESKI_BICIM = (
    ('          _geri_koy_satiri değer "$yol"\n',
     '          echo "        düşerse ESKİ değer yedekte: $YEDEK/vault/$yol — STDIN\'le: vault kv put $yol value=-"\n', 1),
    ('$(_geri_koy_satiri DSN "$DB_KASA_YOL")',
     "        düşerse ESKİ DSN yedekte: $YEDEK/vault/$DB_KASA_YOL — STDIN'le: vault kv put $DB_KASA_YOL value=-", 2),
    ('$(_geri_koy_satiri değer "$CP_KASA_YOL")',
     "        düşerse ESKİ değer yedekte: $YEDEK/vault/$CP_KASA_YOL — STDIN'le: vault kv put $CP_KASA_YOL value=-", 2),
)


def _degistir(tmp_path: pathlib.Path, ad: str, ciftler, kaynak: pathlib.Path = BETIK) -> pathlib.Path:
    """Değiştirilmiş KOPYA — her çapanın sayısı PİNLİ (bulunamayan ya da fazla çapa sessizce yanlış yeri bozardı)."""
    metin = kaynak.read_text(encoding="utf-8")
    for eski, yeni, adet in ciftler:
        _iddia(metin.count(eski) == adet, f"çapa sayısı {metin.count(eski)} ≠ {adet}: {eski!r}")
        metin = metin.replace(eski, yeni)
    hedef = tmp_path / ad
    hedef.write_text(metin, encoding="utf-8")
    hedef.chmod(0o755)
    return hedef


def _beyanli(metin: str) -> tuple[str, list[tuple], list[tuple]]:
    out, yeni, eski = [], [], []
    for s in metin.splitlines():
        d = _coz(s)
        if d and d["args"] and len(d["args"]) == 5:
            yeni.append((d["ne"], *d["args"]))
            out.append(f"<GERİ-KOY {d['ne']} {d['args'][3]} {d['args'][4]}>")
            continue
        m = ESKI_SATIR_DESENI.match(s)
        if m:
            eski.append(m.groups())
            out.append(f"<GERİ-KOY {m.group(1)} {m.group(2)} {m.group(3)}>")
            continue
        out.append(s)
    return "\n".join(out), yeni, eski


def _iz(betik: pathlib.Path, dizin: pathlib.Path, dal: str, bayrak: dict) -> dict:
    """v561 `_iz`in üç dallı ikizi (genel dahil) — ortamın vault/jeton yolunu da (normalize) döndürür."""
    dizin.mkdir()
    dunya, argv, girdi = DAL[dal][:3]
    kok, ortam, log, durum = dunya(dizin, **bayrak)
    once = v557._agac(kok)
    r = _kos(betik, ortam, *argv, girdi=girdi)
    sonra = v557._agac(kok)

    def norm(m: str) -> str:
        return v557._norm(m.replace(str(betik), "<BETIK>"), dizin)

    dosyalar = {v557._norm(rel, dizin): ("YENİ" if rel not in once else "SİLİNDİ" if rel not in sonra
                                         else "AYNI" if once[rel] == sonra[rel] else "DEĞİŞTİ")
                for rel in sorted(set(once) | set(sonra))}
    stderr, yeni, eski = _beyanli(norm(r.stderr))
    return {"rc": r.returncode, "stdout": norm(r.stdout), "stderr": stderr, "olaylar": v556._olaylar(kok),
            "kasa_argv": norm(log.read_text(encoding="utf-8")) if log.exists() else None, "dosyalar": dosyalar,
            "yeni": yeni, "eski": eski,
            "ortam": [_adres(ortam), norm(ortam["VAULT_BIN"]), norm(ortam["VAULT_TOKEN_FILE"])]}


E_SENARYO = (("genel_basari", "genel", {}, 0, 1),
             ("genel_render_yok", "genel", {"SAHTE_RENDER": "yok"}, 2, 1),
             ("genel_put_duser", "genel", {"SAHTE_PUT_IZIN": "0"}, 1, 1),
             ("db_basari", "db", {}, 0, 1),
             ("db_put_duser", "db", {"SAHTE_PUT_IZIN": "0"}, 1, 1),
             ("db_iki_yol_duser", "db", {"SAHTE_ALTER_DUSER": "1", "SAHTE_ROLLBACK_KIRIK": "1", "SAHTE_PUT_IZIN": "1"},
              1, 1),
             ("db_rollback_kirik", "db", {"SAHTE_ALTER_DUSER": "1", "SAHTE_ROLLBACK_KIRIK": "1"}, 1, 0),
             ("cp_basari", "cp", {}, 0, 1),
             ("cp_render_yok", "cp", {"SAHTE_RENDER": "yok"}, 2, 1))


@pytest.mark.parametrize("etiket,dal,bayrak,rc,n", E_SENARYO, ids=[e[0] for e in E_SENARYO])
def test_E1_IZ_eski_bicimli_tabanla_BIREBIR_tek_fark_BEYANLI_satir(tmp_path, etiket, dal, bayrak, rc, n):
    """Kıyas boş değil: yeni izde n TEK SATIR (argümanları betiğin ortamı), tabanda n eski satır; ikisi aynı yedek ve
    yola iner. `db_rollback_kirik` (n=0): db'nin OTOMATİK yedek yolu (betik içi STDIN put) DEĞİŞMEDİ."""
    taban = _degistir(tmp_path, "taban_v568.sh", ESKI_BICIM)
    a = _iz(BETIK, tmp_path / "yeni", dal, bayrak)
    b = _iz(taban, tmp_path / "taban", dal, bayrak)
    for k in ("rc", "stdout", "stderr", "olaylar", "kasa_argv", "dosyalar"):
        _iddia(a[k] == b[k], _maskeli(f"{etiket}: {k} ayrıştı\nyeni={a[k]}\ntaban={b[k]}"))
    _iddia(a["rc"] == rc, f"{etiket}: çıkış {a['rc']} ({rc} bekleniyordu)")
    _iddia(len(a["yeni"]) == n and not a["eski"] and len(b["eski"]) == n and not b["yeni"],
           f"{etiket}: beyanlı satır sayıları yeni {len(a['yeni'])}/{len(a['eski'])} · taban {len(b['yeni'])}/"
           f"{len(b['eski'])} ({n}/0 · 0/{n} bekleniyordu)")
    _iddia(all(list(y[1:4]) == a["ortam"] for y in a["yeni"]), f"{etiket}: TEK SATIR betiğin kasa ortamını taşımıyor")


# =================================================================================================
# M) MUTASYONLAR — mutant tmp'ye yazılır, özgün betik DEĞİŞMEZ
# =================================================================================================

def _mutant(tmp_path: pathlib.Path, ad: str, eski: str, yeni: str) -> pathlib.Path:
    return _degistir(tmp_path, ad, ((eski, yeni, 1),))


def test_M1_MUT_DEGER_ARGVye_konursa_A2_B1_C1_KIRMIZI(tmp_path):
    """Gövde değeri STDIN yerine argv'ye koyar (`value="$(tr … < yedek)"`): statik (A2), gerçek reçete (B1 — kasa
    şimi argv'yi kaydeder) ve odaklı dinamik (C1 — ps + çağrı kaydı) üçü de öter."""
    m = _mutant(tmp_path, "m1.sh", GOVDE_BORU, GOVDE_ARGV)
    _iddia(any("STDIN'e borulanmıyor" in i for i in _a2_ihlalleri(m)), "MUTASYON ISIRMADI (A2)")
    (tmp_path / "b").mkdir()
    ih = _b_ihlalleri(tmp_path / "b", "genel", {"SAHTE_RENDER": "yok"}, 2, betik=m)
    _iddia(any("STDIN biçiminde değil" in i for i in ih) and any(i.startswith("değer #0 ") for i in ih),
           "MUTASYON ISIRMADI (B1): " + _maskeli("\n".join(ih)))
    kok, r, _, yedek, once = _odak_kos(tmp_path, betik=m)
    ih = _odak_ihlalleri(kok, r, yedek, once)
    _iddia("değer #0 argv'de" in ih, "MUTASYON ISIRMADI (C1): " + "\n".join(ih))


def test_M2_MUT_SUDO_kalkarsa_B1_ve_C1_KIRMIZI(tmp_path):
    """Satır `sudo`suz basılır: biçim (B1) ve odaklı dinamik (C1 — kasa çağrıları root kimliğiyle koşmaz; gerçekte
    0600 root yedek ve 0400 jeton ubuntu'ya okunmaz) öter; gerçek reçetede argv kaydında `sudo bash -c` yoktur."""
    m = _mutant(tmp_path, "m2.sh", "sudo bash -c '%s'", "bash -c '%s'")
    (tmp_path / "b").mkdir()
    ih = _b_ihlalleri(tmp_path / "b", "cp", {"SAHTE_RENDER": "yok"}, 2, betik=m)
    _iddia(any("biçiminde değil" in i for i in ih) and "satır sudo'dan geçmedi (argv kaydında `sudo bash -c` yok)" in ih,
           "MUTASYON ISIRMADI (B1): " + _maskeli("\n".join(ih)))
    kok, r, _, yedek, once = _odak_kos(tmp_path, betik=m)
    ih = _odak_ihlalleri(kok, r, yedek, once)
    _iddia("kasa çağrıları root kimliğiyle koşmadı (sudo yok)" in ih, "MUTASYON ISIRMADI (C1): " + "\n".join(ih))


def test_M3_MUT_BIR_DALDA_ESKI_BICIM_geri_gelirse_A1_ve_B1_KIRMIZI(tmp_path):
    """`--cp --vault`un İLK (kasa evresi) satırı 9cf96240'ın açıklamasına döner: tek-kaynak çivisi (A1) ve o evrenin
    gerçek reçetesi (B1) öter."""
    eski, yeni, _ = ESKI_BICIM[2]
    m = _mutant(tmp_path, "m3.sh", eski + "\n     2) render hedefi ($CP_KASA_HEDEF) kasadaki ESKİ değere dönene",
                yeni + "\n     2) render hedefi ($CP_KASA_HEDEF) kasadaki ESKİ değere dönene")
    ih = _a1_ihlalleri(m)
    _iddia(any(i.startswith("_cp_kasa_recetesi: yardımcı çağrısı 1") for i in ih)
           and "eski biçim (açıklama) satırı kodda duruyor" in ih, "MUTASYON ISIRMADI (A1): " + "\n".join(ih))
    ih = _b_ihlalleri(tmp_path, "cp", {"SAHTE_RENDER": "yok"}, 2, betik=m)
    _iddia("eski biçim (açıklama) satırı VAR" in ih and "koşulacak TEK SATIR yok" in ih,
           "MUTASYON ISIRMADI (B1): " + _maskeli("\n".join(ih)))


def test_M4_MUT_BOS_YEDEK_KAPISI_kalkarsa_C2_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m4.sh", GOVDE_KAPI, "")
    kok, r, _, _, _ = _odak_kos(tmp_path, betik=m, yedek_icerik=None)
    ih = _yazim_yok_ihlalleri(kok, r, "yedek yok/boş")
    _iddia("kasaya YAZIM denendi" in ih, "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M5_MUT_TRAP_kalkarsa_C1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m5.sh", GOVDE_TRAP, "")
    kok, r, _, yedek, once = _odak_kos(tmp_path, betik=m)
    ih = _odak_ihlalleri(kok, r, yedek, once)
    _iddia("geçici HOME silinmedi — yönetici oturumu diskte kaldı" in ih, "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M6_MUT_LOGIN_HOME_yalitimi_kalkarsa_C1_KIRMIZI(tmp_path):
    """Login geçici HOME'suz koşar: oturum kullanıcının HOME'una düşer (kalıcı yönetici oturumu) ve put onu görmez."""
    m = _mutant(tmp_path, "m6.sh", GOVDE_LOGIN, '"$2" login -no-print - < "$3"')
    kok, r, _, yedek, once = _odak_kos(tmp_path, betik=m)
    ih = _odak_ihlalleri(kok, r, yedek, once)
    _iddia("yönetici oturumu kullanıcının HOME'una düştü" in ih, "MUTASYON ISIRMADI: " + "\n".join(ih))

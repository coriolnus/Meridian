"""test_sir_kasa_yedek_v567.py — TSK-064(b): genel kasa döngüsünde `kv rollback` DÜŞERSE yedek yol — ESKİ kasa değeri
yazımdan ÖNCE yedeklenir, reçete onu STDIN'le geri koymayı söyler (2026-09-27).

NUMARA: `ls tests | grep _v567` boş (ana checkout + bütün worktree'ler tarandı 2026-09-27; en yüksek v565, v566
paralel ajanın).

BAĞLAM (TSK-064 kasa sürümü dilimi incelemesi, ORTA — Rol-1 doğruladı). `sir_rotasyon.sh`in genel kasa döngüsü
(`vault_rotasyon`: kapi · tenant [+ takma ad] · dash · apisix-admin · openrouter; `--uret`li ya da istemli) `kv put`
ÖNCESİ sürümü kaydediyor ve reçetede önce `vault kv rollback -version=N` veriyordu. AMA `kv rollback`un KENDİSİ düşerse
(politika · ağ · mühür) genel yolda yedek yol YOKTU: eski kasa DEĞERİ hiç okunmuyordu. `--db`/`--cp` dalları bunu
zaten yapıyordu (ESKİ değeri KASADAN okuyup `$YEDEK/vault/<yol>`a 0600 yedekler; reçete "düşerse … STDIN'le: vault
kv put <yol> value=-" der). Bu dilim AYNI yöntemi genel döngüye getirir.

ROL-1 KARARI (brief): yedek, sürümün kaydedildiği AYNI noktada, emsalin AYNI yöntemiyle alınır (konum/izin emsalle
aynı; değer HİÇBİR çıktıya, argv'ye, log'a düşmez). Reçete: 1) `vault kv rollback -version=N <yol>`; düşerse 2) yedekten
ESKİ değer STDIN'le `kv put`; 3) dosya adımı. Yol yoksa (ilk yazım) sürüm kapısı zaten durdurur — davranış korunur.
`--kuru` yeni adımı "yedeklenir" diye söyler. db/cp dalları BİREBİR; `--uret` ve istem aynı.

DÜZENEK — ŞİMLER YENİDEN YAZILMADI: v561 `_dunya` (v556 CP dünyası: v447 sahte kök + KV v2 sahte kasa + sahte Agent;
ayırt edici kasa tohumları; `kv metadata get` sarmalayıcısı). Bu dosya üstüne YALNIZ iki sarmalayıcı ekler:
  · `vault` — `SAHTE_ROLLBACK_KIRIK=1` iken `kv rollback` düşer (yedek yolun sahnesi), `SAHTE_GET_KIRIK=1` iken
    (`SAHTE_GET_KIRIK_YOL` verilirse YALNIZ o yolda) `kv get` düşer; `SAHTE_PS_DIZIN` verilirse her `kv` çağrısında
    süreç tablosu görüntüsü alır. Öteki her çağrı alttaki şimlere AYNEN gider.
  · `sudo` — `SAHTE_PS_DIZIN` verilirse görüntü alır (kendi argv'si dahil), sonra v447 `sudo` şimine devreder.
DİNAMİK ARGV ÖLÇÜMÜ (v552/v556 deseni): görüntülerden YALNIZ bu pytest sürecinin torunları okunur (`_torunlar`) —
başka worktree'deki koşumlar sahte kırmızı üretmesin.

BÖLÜMLER
  A  sözleşme — üç dal AYNI yedek yöntemi (ayrışma çivisi) · genel döngüde sıra · reçete satırının biçimi
  B  kuru — her kasa yolu için "ESKİ değer yedeği: yedeklenir" satırı; kasaya çağrı YOK, dosya yazımı YOK
  C  gerçek — yedek put'tan ÖNCE · içerik yazım ÖNCESİ değer · izin emsalle AYNI · reçetede rollback → STDIN kv put
     → dosya · rollback düşünce yedek yol kasayı ESKİ değere döndürür · iki sırlı tur · kapıda düşen ikinci sır · put
     düşer · kv get düşer · dinamik ps
  D  yol yok / sürüm okunamaz — sürüm kapısı ÖNCE durdurur: kv get YOK, yedek YOK (davranış korunur)
  E  db/cp BİREBİR — bu dilimin ekleri çıkarılmış betikle İZ KIYASI (aynı dünya, aynı senaryo)
  M  MUTASYONLAR — brief'in dördü (yedeklemeyi kaldır · değeri argv'ye koy · reçete sırasını boz · yedek iznini
     gevşet) + reçetede değer argv'de · kuru satırı · kv get düşüşü yutulur · yedek put'tan SONRA

SIR DEĞERİ YOK: tohumlar `SAHTE-` önekli ve sahtedir. İddialar bool'a indirilir (`_iddia` — pytest içgözlemi işlenenleri
HAM basmasın); mesajlar yalnız ad/etiket ya da maskeli metin taşır. Bu dosyanın maskesi v561'in kısa tohumlarını da
kapsar (v561 incelemesinin DÜŞÜK bulgusu: v557 `_TOHUMLAR` onları görmüyordu).

TSK-237 (2026-09-27, v568): reçetenin "rollback düşerse" satırı artık açıklama DEĞİL, operatörün A1'de koşacağı TEK SATIR
komuttur (`_geri_koy_satiri`, üç dalın ortak yardımcısı). Satırın biçimi, çözücüsü ve koşturucusu v568'de yaşar (tek
kaynak); bu dosya reçete iddialarını oradan alır (A3 yardımcı çağrısını sayar, C3 satırı YAZILDIĞI GİBİ koşar, E1 çapası
yardımcı çağrısıdır, M2b gövdenin STDIN borusunu argv'ye çevirir). Yedek YÖNTEMİ (A1/A2/C/D) değişmedi.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import stat
import subprocess
import sys

import pytest

from tests import test_cp_rotasyon_v556 as v556
from tests import test_sir_kasa_surum_v561 as v561
from tests import test_sir_recete_tek_satir_v568 as v568
from tests import test_sir_uret_v557 as v557
from tests import test_vault_db_kasa_v538 as v538
from tests import test_vault_dalga1_baglama_v521 as v521
from tests.test_sir_rotasyon_v447 import BETIK, ENVANTER, ESKI, _dosya_imzalari, _kos

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]

TENANT_YOLU = v561.TENANT_YOLU
TAKMA_TENANT = v561.TAKMA_TENANT
NOUS_YOLU = v561.NOUS_YOLU
LLM_YOLU = v561.LLM_YOLU
TAKMA_OR = v561.TAKMA_OR
CP_YOLU = v556.KASA_YOLU
ISTEM_DEGERI = "SAHTE-ISTEM-0567"

#: Betiğin basacağı satırlar — BİREBİR.
YEDEK_OLDU = "  ✓ yedek: ESKİ değer (KASADAN) → {yedek}/vault/{yol} (0600 — geri almanın girdisi)"
#: Reçetenin yedek yol satırı — TSK-237'den beri TEK SATIR komut; biçim ve çözücü v568'de (tek kaynak).
YEDEK_ONEKI = v568.YEDEK_ONEKI
KURU_YEDEK = ("  ESKİ değer yedeği: yedeklenir — kv put ÖNCESİ KASADAN okunur → {kok}/root/sir-yedek-<UTC ts>-{alt}/vault/"
              "{yol} (0600); rollback düşerse STDIN'le: vault kv put {yol} value=- (değer BASILMAZ; okunamazsa bu yol "
              "YAZILMAZ)")
GET_OKUNAMADI = ("!! ESKİ değer kasadan okunamadı ({yol}) — rollback düşerse geri konacak yedek olmadan kasaya YAZILMAZ "
                 "({neden})")

#: Maskelenecek bilinen tohumlar — v557'ninkiler + v561'in KISA tohumları + bu dosyanınki.
_TOHUMLAR = v557._TOHUMLAR + (v561.ONCEKI_TENANT, v561.ONCEKI_NOUS, v561.LLM_V1, v561.LLM_V2, v561.YENI_NOUS,
                              v561.YENI_OR, ISTEM_DEGERI)

SIM_VAULT_V567 = '''#!__PY__
"""v567 `vault` sarmalayıcısı. `SAHTE_ROLLBACK_KIRIK=1` → `kv rollback` düşer; `SAHTE_GET_KIRIK=1` → `kv get` düşer
(`SAHTE_GET_KIRIK_YOL` verilirse YALNIZ o yolda); `SAHTE_PS_DIZIN` → her `kv` çağrısında süreç tablosu görüntüsü.
Öteki her çağrı alttaki şime AYNEN gider. Değer taşımaz: yalnız yol ve olay adı."""
import os, subprocess, sys
ASIL = __ASIL__
a = sys.argv[1:]


def olay(s):
    with open(os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "argv.log"), "a", encoding="utf-8") as fh:
        fh.write("OLAY " + s + "\\n")


def goruntu():
    d = os.environ.get("SAHTE_PS_DIZIN")
    if d:
        r = subprocess.run(["ps", "-A", "-ww", "-o", "pid=,ppid=,args="], capture_output=True, text=True)
        with open(os.path.join(d, "ps_%04d.txt" % len(os.listdir(d))), "w", encoding="utf-8") as fh:
            fh.write(r.stdout)


if a[:1] == ["kv"]:
    goruntu()
if a[:2] == ["kv", "rollback"] and os.environ.get("SAHTE_ROLLBACK_KIRIK") == "1":
    olay("kv-rollback-DUSTU " + a[-1])
    sys.stderr.write("Error writing data to %s: permission denied\\n" % a[-1])
    sys.exit(2)
if (a[:2] == ["kv", "get"] and os.environ.get("SAHTE_GET_KIRIK") == "1"
        and os.environ.get("SAHTE_GET_KIRIK_YOL", a[-1]) == a[-1]):
    olay("kv-get-DUSTU " + a[-1])
    sys.stderr.write("Error reading %s: permission denied\\n" % a[-1])
    sys.exit(2)
os.execv(ASIL, [ASIL] + a)
'''

SIM_SUDO_V567 = '''#!__PY__
"""`SAHTE_PS_DIZIN` verilirse süreç tablosu görüntüsü alır (bu sürecin argv'si dahil), sonra v447 `sudo` şimine
AYNEN devreder."""
import os, subprocess, sys
d = os.environ.get("SAHTE_PS_DIZIN")
if d:
    r = subprocess.run(["ps", "-A", "-ww", "-o", "pid=,ppid=,args="], capture_output=True, text=True)
    with open(os.path.join(d, "ps_%04d.txt" % len(os.listdir(d))), "w", encoding="utf-8") as fh:
        fh.write(r.stdout)
os.execv(__ASIL__, [__ASIL__] + sys.argv[1:])
'''

_BAYRAKLAR = ("SAHTE_ROLLBACK_KIRIK", "SAHTE_GET_KIRIK", "SAHTE_GET_KIRIK_YOL", "SAHTE_PS_DIZIN")


# =================================================================================================
# YARDIMCILAR
# =================================================================================================

_iddia = v557._iddia


def _maskeli(metin: str) -> str:
    for d in _TOHUMLAR:
        metin = metin.replace(d, "<SAHTE-TOHUM>")
    return re.sub(r"[A-Za-z0-9_+=-]{40,}", "<UZUN-JETON>", metin)


def _ozet(r: subprocess.CompletedProcess) -> str:
    return f"çıkış {r.returncode}\n--- stdout ---\n{_maskeli(r.stdout)}\n--- stderr ---\n{_maskeli(r.stderr)}"


def _dunya(tmp_path: pathlib.Path, **bayrak: str):
    """v561 dünyası (v556 CP dünyası + ayırt edici kasa tohumları + metadata sarmalayıcısı) + bu dosyanın iki
    sarmalayıcısı. `bayrak`: SAHTE_* ortamı (v561'inkiler dahil — çalışma anında okunur)."""
    kok, ortam, log, durum = v561._dunya(tmp_path)
    binn = tmp_path / "bin_v567"
    binn.mkdir()
    for ad, govde, asil in (("vault", SIM_VAULT_V567, ortam["VAULT_BIN"]),
                            ("sudo", SIM_SUDO_V567, str(tmp_path / "bin" / "sudo"))):
        (binn / ad).write_text(govde.replace("__PY__", sys.executable).replace("__ASIL__", repr(asil)),
                               encoding="utf-8")
        (binn / ad).chmod(0o755)
    ortam = dict(ortam, VAULT_BIN=str(binn / "vault"), PATH=f"{binn}:{ortam['PATH']}")
    for b in _BAYRAKLAR:
        ortam.pop(b, None)
    ortam.update(bayrak)
    return kok, ortam, log, durum


def _yedek_dizini(kok: pathlib.Path, alt: str) -> pathlib.Path | None:
    adaylar = sorted((kok / "root").glob(f"sir-yedek-*-{alt}"))
    return adaylar[0] if len(adaylar) == 1 else None


def _mod(p: pathlib.Path) -> int | None:
    return stat.S_IMODE(p.stat().st_mode) if p.exists() else None


def _izinler(yedek: pathlib.Path, yol: str) -> tuple[int | None, int | None, int | None]:
    """(yedek dizini, kasa yedeğinin dizini, kasa yedeği) modları — emsal kıyasının birimi."""
    dosya = yedek / "vault" / yol
    return _mod(yedek), _mod(dosya.parent), _mod(dosya)


def _olaylar(kok: pathlib.Path) -> list[str]:
    return v556._olaylar(kok)


def _ilk_indeks(ol: list[str], onek: str) -> int | None:
    for i, o in enumerate(ol):
        if o == onek or o.startswith(onek + " "):
            return i
    return None


def _yedek_ihlalleri(r: subprocess.CompletedProcess, kok: pathlib.Path, alt: str,
                     beklenen: list[tuple[str, str]], yok: tuple[str, ...] = ()) -> list[str]:
    """Her (yol, yazım ÖNCESİ değer) için: kv get TAM bir kez, metadata'dan SONRA put'tan ÖNCE · yedek dosyası var ·
    içerik yazım ÖNCESİ değer (bool) · izin (0700 dizin, 0600 dosya) · `oldu` satırı. `yok` yolları için kv get YOK,
    yedek YOK. Değer BASILMAZ."""
    ih = []
    yedek = _yedek_dizini(kok, alt)
    if yedek is None:
        return [f"tam bir '{alt}' yedek dizini yok"]
    ol = _olaylar(kok)
    for yol, onceki in beklenen:
        get = [i for i, o in enumerate(ol) if o == f"kv-get {yol}"]
        meta, put = _ilk_indeks(ol, f"kv-metadata {yol}"), _ilk_indeks(ol, f"kv-put {yol}")
        if len(get) != 1:
            ih.append(f"{yol}: kv get {len(get)} kez (1 bekleniyordu)")
        elif meta is None or get[0] < meta:
            ih.append(f"{yol}: ESKİ değer sürüm kaydından ÖNCE okundu (sürüm kapısı ilk söz almalı)")
        elif put is not None and get[0] > put:
            ih.append(f"{yol}: ESKİ değer put'tan SONRA okundu")
        dosya = yedek / "vault" / yol
        if not dosya.is_file():
            ih.append(f"{yol}: yedek dosyası YOK ({dosya.relative_to(kok)})")
            continue
        if dosya.read_text(encoding="utf-8").strip("\r\n") != onceki:
            ih.append(f"{yol}: yedek içeriği yazım ÖNCESİ kasa değeri DEĞİL")
        izin = _izinler(yedek, yol)
        if izin != (0o700, 0o700, 0o600):
            ih.append(f"{yol}: izinler {tuple(oct(x) if x is not None else None for x in izin)} ≠ (0o700, 0o700, 0o600)")
        if YEDEK_OLDU.format(yedek=yedek, yol=yol) not in r.stdout.splitlines():
            ih.append(f"{yol}: stdout'ta 'yedek: ESKİ değer (KASADAN)' satırı yok")
    for yol in yok:
        if f"kv-get {yol}" in ol:
            ih.append(f"{yol}: yazılmayacak yol için kv get")
        if (yedek / "vault" / yol).exists():
            ih.append(f"{yol}: yazılmayacak yol için yedek dosyası")
    return ih


def _recete_yedek_ihlalleri(r: subprocess.CompletedProcess, yedek: pathlib.Path | None, yollar: list[str],
                            yok: tuple[str, ...] = ()) -> list[str]:
    """Kasa evresi reçetesi: her yol için TAM bir yedek yol satırı · rollback satırının HEMEN ARDINDA · DOSYA
    adımından ÖNCE · TEK SATIR komut, değer dosyadan STDIN'e borulanır (argv'de değer yok; biçim v568) · `yok` yolları
    için yedek yol YOK."""
    ih = []
    rec = v561._recete(r.stderr)
    if not rec:
        return ["geri alma reçetesi basılmadı"]
    dosya = v561._satir_indeksi(rec, v561.DOSYA_ADIMI)
    for s in rec:
        if s.startswith("        düşerse"):
            d = v568._coz(s)
            if d is None or v568._yedek_ve_yol(s) is None or not v568._stdin_govdesi(d["govde"]):
                ih.append("yedek yol satırı STDIN biçiminde değil (TEK SATIR `sudo bash -c` + dosya → STDIN boru dışında)")
    n = sum(s.startswith(YEDEK_ONEKI) for s in rec)
    if n != len(yollar):
        ih.append(f"yedek yol satırı sayısı {n} ≠ {len(yollar)}")
    for yol in yollar:
        rb = [i for i, s in enumerate(rec) if s.startswith("        vault kv rollback ") and s.endswith(" " + yol)]
        yd = [i for i, s in enumerate(rec) if yedek is not None and v568._yedek_ve_yol(s) == (f"{yedek}/vault/{yol}", yol)]
        if len(yd) != 1 or len(rb) != 1:
            ih.append(f"{yol}: reçetede rollback {len(rb)} · yedek yol {len(yd)} satırı (1/1 bekleniyordu)")
            continue
        if yd[0] != rb[0] + 1:
            ih.append(f"{yol}: yedek yol satırı rollback satırının HEMEN ARDINDA değil")
        if dosya is None or yd[0] > dosya:
            ih.append(f"{yol}: yedek yol satırı DOSYA adımından SONRA")
    for yol in yok:
        if any(s.startswith(YEDEK_ONEKI) and (v568._yedek_ve_yol(s) or ("", ""))[1] == yol for s in rec):
            ih.append(f"{yol}: yedeği ALINMAMIŞ yol için yedek yol önerildi")
    return ih


def _yedek_yolunu_uygula(r: subprocess.CompletedProcess, ortam: dict, yol: str) -> list[str]:
    """Reçetenin yedek yol satırı YÜRÜTÜLÜR (sahte kasada, YAZILDIĞI GİBİ — TSK-237'den beri TEK SATIR komut, v568):
    gösterdiği dosya gerçek yedek · komut `sudo bash -c '<gövde>' _ <adres> <vault> <jeton> <yedek> <yol>` · değer
    dosyadan STDIN'e borulanır (betiğin `tr -d '\\r\\n'` kırpması gövdede)."""
    ds = [d for d in (v568._coz(s) for s in v561._recete(r.stderr))
          if d and d["args"] and len(d["args"]) == 5 and d["args"][4] == yol and v568._stdin_govdesi(d["govde"])]
    if len(ds) != 1:
        return [f"reçetede {yol} için STDIN biçimli TEK yedek yol satırı yok ({len(ds)})"]
    if not pathlib.Path(ds[0]["args"][3]).is_file():
        return ["reçetenin gösterdiği yedek dosyası YOK"]
    y = v568._satiri_kos(ds[0]["komut"], ortam)
    return [] if y.returncode == 0 else ["yedek yol komutu sahte kasada koşmadı"]


#: Süreç görüntüsü okuyucusu v568'de (tek kaynak; v552/v556 deseni).
_ps_goruntuleri = v568._ps_goruntuleri


def _ps_ihlalleri(dizin: pathlib.Path, yol: str, *degerler: str) -> list[str]:
    """Pozitif kontrol: görüntüler kv get'in ve yedek yazımının argv'sini GÖRÜYOR. Negatif: değer (ve sha256'sının ilk 8
    hanesi) hiçbir torun sürecin argv'sinde YOK. Mesaj değeri basmaz, sırasını söyler."""
    g = _ps_goruntuleri(dizin)
    if not g:
        return ["süreç tablosu görüntüsü YOK — ölçülemedi"]
    argvler = [a for x in g for a in x]
    ih = []
    if not any(f"kv get -field=value {yol}" in a for a in argvler):
        ih.append("POZİTİF KONTROL: ps `kv get` argv'sini görmedi")
    if not any("yardimci.py cikar dosya" in a and "vault_eski_ham" in a for a in argvler):
        ih.append("POZİTİF KONTROL: ps yedek yazımının argv'sini görmedi")
    for i, d in enumerate(degerler):
        h8 = hashlib.sha256(d.encode()).hexdigest()[:8]
        n = sum(d in a for a in argvler)
        if n:
            ih.append(f"değer #{i} {n} süreç argv'sinde")
        if any(h8 in a for a in argvler):
            ih.append(f"değer #{i} HASH'i süreç argv'sinde")
    return ih


# =================================================================================================
# A) SÖZLEŞME — üç dal AYNI yöntem (ayrışma çivisi), genel döngüde sıra, reçete biçimi
# =================================================================================================

def _yorumsuz(metin: str) -> str:
    return "\n".join(s for s in metin.splitlines() if not s.lstrip().startswith("#"))


KV_GET_DESENI = re.compile(r'\(\s*umask 077;\s*_vault kv get -field=value "\$yol" > "\$ISLIK/(\w+)"\s*\)')
INSTALL_DESENI = re.compile(r'sudo install -d -m (0\d{3}) -o (\w+) -g (\w+) "\$YEDEK/vault/\$\(dirname "\$yol"\)"')
CIKAR_DESENI = re.compile(r'py cikar dosya "\$ISLIK/(\w+)" - - "\$YEDEK/vault/\$yol"')
DALLAR = ("vault_rotasyon", "vault_db_rotasyon", "vault_cp_rotasyon")


def test_A0_ITHAL_EDILEN_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v556/v557/v561 A0): ithal edilen modül başka ağaçtan yüklenirse çiviler BAŞKA betiği ölçer."""
    for yol in (BETIK, ENVANTER, pathlib.Path(v556.__file__), pathlib.Path(v557.__file__),
                pathlib.Path(v561.__file__), pathlib.Path(v538.__file__), pathlib.Path(v521.__file__)):
        assert yol.resolve().is_relative_to(KOK_DEPO.resolve()), f"yabancı ağaçtan ithal: {yol}"


def _yontem(dal: str, betik: pathlib.Path = BETIK) -> dict:
    govde = _yorumsuz(v521._fonksiyon(dal, betik))
    return {"get": KV_GET_DESENI.findall(govde), "install": INSTALL_DESENI.findall(govde),
            "cikar": CIKAR_DESENI.findall(govde), "govde": govde}


def test_A1_AYRISMA_CIVISI_uc_dal_AYNI_yedek_yontemi_kasadan_0700_0600():
    """Tek-kaynak yasası — kopya kaçınılmaz (db/cp dalları BİREBİR kalır), ayrışma çivisi: üç dalın her biri ESKİ
    değeri TAM bir kez `( umask 077; _vault kv get -field=value "$yol" > <0600 dosya> )` ile KASADAN okur, TAM bir kez
    `$YEDEK/vault/<dirname>`i AYNI mod/sahiple kurar ve TAM bir kez `py cikar … "$YEDEK/vault/$yol"` ile yazar. Biri
    izni gevşetir ya da değeri başka kaynaktan alırsa öter. Genel dalda yedeğin kaynağı kv get'in çıktısının KENDİSİ."""
    y = {d: _yontem(d) for d in DALLAR}
    for d, v in y.items():
        _iddia(len(v["get"]) == 1 and len(v["install"]) == 1 and len(v["cikar"]) == 1,
               f"{d}: kv get {len(v['get'])} · install {len(v['install'])} · cikar {len(v['cikar'])} (1/1/1 bekleniyordu)")
    kurulum = {d: v["install"][0] for d, v in y.items()}
    _iddia(len(set(kurulum.values())) == 1 and kurulum["vault_rotasyon"] == ("0700", "root", "root"),
           f"yedek dizini kurulumu dallar arasında ayrıştı: {kurulum}")
    genel = y["vault_rotasyon"]
    _iddia(genel["get"][0] == genel["cikar"][0], "genel dal: yedeğin kaynağı kasadan okunan dosya DEĞİL")
    # TSK-237: reçetenin TEK SATIRI yedeği dalların YAZDIĞI yerden okur — yardımcı `"$YEDEK/vault/$2"` (2. argüman = dalın
    # kendi yol değişkeni, A3) ↔ üç dalın yazım hedefi `"$YEDEK/vault/$yol"` (CIKAR_DESENI). Biri taşınırsa öteki izlemeli.
    yardimci = _yorumsuz(v521._fonksiyon(v568.YARDIMCI))
    _iddia(yardimci.count('"$YEDEK/vault/$2"') == 1 and all(v["cikar"] for v in y.values()),
           "reçetenin okuduğu yedek yeri dalların yazdığı yerden ayrıştı")


def test_A2_GENEL_DONGU_sira_surum_kapisi_ESKI_deger_yedek_satir_put():
    """Sürüm kapısı ÖNCE (yol yoksa hata metni DEĞİŞMEZ) → kv get → yedek dizini → yedek → reçete satırı/evre → put.
    Satır yedekten SONRA: okunamayan yedek reçeteye yedeksiz bir güvence yazamaz."""
    g = _yontem("vault_rotasyon")["govde"]
    parcalar = ('_kasa_surumu "$yol"', "_vault kv get -field=value", "sudo install -d -m 0700",
                'py cikar dosya "$ISLIK/vault_eski_ham"', 'GENEL_KASA_SATIRLARI="$GENEL_KASA_SATIRLARI',
                '_vault kv put "$yol" value=-')
    yerler = [g.find(p) for p in parcalar]
    _iddia(all(x >= 0 for x in yerler) and yerler == sorted(yerler),
           f"genel döngüde sıra bozuk: {list(zip(parcalar, yerler))}")


def test_A3_RECETE_yedek_yol_satiri_UC_dalda_AYNI_yardimcidan_TEK_SATIR():
    """TSK-237: reçetenin yedek yol satırı üç dalda AYNI yardımcıdan (`_geri_koy_satiri`) — her rollback satırı kadar
    çağrı (genel 1 · cp 2 · db 2), doğru ad (değer/DSN) ve dalın KENDİ yol değişkeni; eski açıklama biçimi hiçbir kod
    satırında yok, etiket metni yardımcı dışında kopyalanmamış. Ölçüm v568 A1'in listesidir (tek kaynak)."""
    ih = v568._a1_ihlalleri()
    _iddia(not ih, "\n".join(ih))


# =================================================================================================
# B) KURU — "yedeklenir" satırı
# =================================================================================================

def _kuru_ihlalleri(r, kok, log, alt, yollar) -> list[str]:
    ih = [] if r.returncode == 0 else [f"çıkış {r.returncode}"]
    satirlar = r.stdout.splitlines()
    for yol in yollar:
        i = next((j for j, s in enumerate(satirlar) if s.startswith(v561.KURU_SATIRI.format(yol=yol))), None)
        if i is None:
            ih.append(f"{yol}: 'kasa sürümü' satırı yok")
        elif i + 1 >= len(satirlar) or satirlar[i + 1] != KURU_YEDEK.format(kok=kok, alt=alt, yol=yol):
            ih.append(f"{yol}: 'kasa sürümü' satırını 'ESKİ değer yedeği: yedeklenir' satırı İZLEMİYOR")
    if sum("ESKİ değer yedeği: yedeklenir" in s for s in satirlar) != len(yollar):
        ih.append("'yedeklenir' satırı sayısı kasa yolu sayısına eşit değil")
    if log.exists():
        ih.append("kuru koşum kasaya çağrı yaptı")
    return ih


@pytest.mark.parametrize("alt", sorted(v561.KURU_ALTLAR))
def test_B1_KURU_her_kasa_yolu_icin_ESKI_deger_YEDEKLENIR_satiri_KASAYA_cagri_YOK(tmp_path, alt):
    kok, ortam, log, _ = _dunya(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, f"--{alt}", "--vault", "--kuru")
    ih = _kuru_ihlalleri(r, kok, log, alt, v561.KURU_ALTLAR[alt])
    if _dosya_imzalari(kok) != once:
        ih.append("kuru koşum dosya yazdı")
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


# =================================================================================================
# C) GERÇEK KOŞUM
# =================================================================================================

def _kos_tenant(tmp_path: pathlib.Path, kip: str = "uret", betik: pathlib.Path = BETIK, **bayrak: str):
    kok, ortam, log, durum = _dunya(tmp_path, **bayrak)
    if kip == "uret":
        r = _kos(betik, ortam, "--tenant", "--vault", "--uret")
    else:
        r = _kos(betik, ortam, "--tenant", "--vault", girdi=f"{ISTEM_DEGERI}\n")
    return r, kok, ortam, log, durum


def _tenant_ihlalleri(r, kok, log, durum) -> list[str]:
    """`--tenant --vault` başarı koşumunun yedek iddiaları — C1 ve mutasyon çivileri AYNI liste."""
    ih = [] if r.returncode == 0 else [f"çıkış {r.returncode} (0 bekleniyordu)"]
    kasa = v561._kasa(durum, TENANT_YOLU)
    if len(kasa) != 3:
        ih.append(f"kasada {len(kasa)} sürüm (3 bekleniyordu)")
    ih += _yedek_ihlalleri(r, kok, "tenant", [(TENANT_YOLU, ESKI["tenant"])], yok=(TAKMA_TENANT,))
    if any(TAKMA_TENANT in o for o in _olaylar(kok)):
        ih.append("takma adın yoluna kasa çağrısı — yedek BİRİNCİL yoldan alınır")
    ih += _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "tenant"), [TENANT_YOLU])
    ih += v557._sizinti(r, kok, log, kasa[-1] if kasa else "", ESKI["tenant"], v561.ONCEKI_TENANT, ISTEM_DEGERI)
    return ih


@pytest.mark.parametrize("kip", ["uret", "istem"])
def test_C1_BASARI_ESKI_deger_put_tan_ONCE_KASADAN_yedeklenir_recete_rollback_STDIN_dosya(tmp_path, kip):
    """Yedek yazım ÖNCESİ kasa değeridir (tohum: ONCEKI → ESKI; yedek ESKI olmalı, ONCEKI ya da YENİ değil), dosya 0600
    dizin 0700, takma adın yolu çağrılmaz; başarıda da reçete basılır ve yedek yol satırı rollback'in HEMEN ardında,
    dosya adımından ÖNCE; değer hiçbir yüzeyde yok. `--uret` ile istem aynı."""
    r, kok, _, log, durum = _kos_tenant(tmp_path, kip)
    ih = _tenant_ihlalleri(r, kok, log, durum) + v561._recete_ihlalleri(r, [(TENANT_YOLU, 2)])
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_C2_IZIN_ve_KONUM_CP_emsaliyle_AYNI(tmp_path):
    """Brief: yedek konumu/izni emsalle aynı. AYNI şim dünyasında `--cp --vault` (emsal) ile `--tenant --vault`un
    yedek dizini · kasa yedeği dizini · kasa yedeği modları BİREBİR ve konum `<yedek>/vault/<kasa yolu>`."""
    (tmp_path / "genel").mkdir()
    r, kok, _, _, _ = _kos_tenant(tmp_path / "genel")
    _iddia(r.returncode == 0, _ozet(r))
    (tmp_path / "cp").mkdir()
    kok_cp, ortam_cp, _, _ = _dunya(tmp_path / "cp")
    r_cp = _kos(BETIK, ortam_cp, "--cp", "--vault")
    _iddia(r_cp.returncode == 0, _ozet(r_cp))
    genel = _izinler(_yedek_dizini(kok, "tenant"), TENANT_YOLU)
    emsal = _izinler(_yedek_dizini(kok_cp, "cp"), CP_YOLU)
    _iddia(None not in emsal and genel == emsal, f"izin/konum ayrıştı: genel {genel} ↔ cp {emsal}")


def test_C3_ROLLBACK_DUSERSE_yedek_yol_kasayi_yazim_ONCESI_degere_dondurur(tmp_path):
    """Bulgunun kendisi: kasa YENİ değerde, render gelmedi (çıkış 2). Reçetenin rollback satırı yürütülür ve DÜŞER
    (politika/ağ/mühür sahnesi) — kasa YENİ değerde kalır. Sonra reçetenin yedek yol satırı YAZILDIĞI GİBİ
    yürütülür: gösterdiği dosya gerçek yedektir, komut `vault kv put <yol> value=-`dir (argv'de değer yok), girdi
    STDIN'dir — ve kasadaki güncel değer yazım ÖNCESİ değer olur."""
    r, kok, ortam, log, durum = _kos_tenant(tmp_path, SAHTE_RENDER="yok")
    ih = [] if r.returncode == 2 else [f"çıkış {r.returncode} (render aşımı → 2 bekleniyordu)"]
    ih += _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "tenant"), [TENANT_YOLU])
    _iddia(not ih and len(v561._kasa(durum, TENANT_YOLU)) == 3, "\n".join(ih) + "\n" + _ozet(r))
    rb = next(s for s in v561._recete(r.stderr) if s.startswith("        vault kv rollback "))
    d = subprocess.run([ortam["VAULT_BIN"], *rb.split()[1:]], capture_output=True, text=True,
                       env=dict(ortam, SAHTE_ROLLBACK_KIRIK="1"))
    _iddia(d.returncode != 0 and len(v561._kasa(durum, TENANT_YOLU)) == 3, "sahne kurulamadı: rollback DÜŞMEDİ")
    ih = _yedek_yolunu_uygula(r, ortam, TENANT_YOLU)
    _iddia(not ih, "\n".join(ih))
    _iddia(v561._kasa(durum, TENANT_YOLU)[-1] == ESKI["tenant"],
           "yedek yol izlenince kasa yazım ÖNCESİ değere DÖNMEDİ")


def test_C4_IKI_SIRLI_TUR_her_yol_KENDI_yedegiyle_TAKMA_AD_yolu_YOK(tmp_path):
    """`--openrouter --vault`: NOUS ve LLM birincil yolu AYRI yedeklenir (her biri kendi yazım ÖNCESİ değeriyle);
    takma adın (`openrouter_api_key`) yoluna kv get YOK; reçetede her rollback'i KENDİ yedek yol satırı izler."""
    kok, ortam, log, durum = _dunya(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", "--vault", girdi=f"{v561.YENI_NOUS}\n{v561.YENI_OR}\n")
    ih = [] if r.returncode == 0 else [f"çıkış {r.returncode}"]
    ih += _yedek_ihlalleri(r, kok, "openrouter", [(NOUS_YOLU, ESKI["nous"]), (LLM_YOLU, ESKI["or"])], yok=(TAKMA_OR,))
    ih += _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "openrouter"), [NOUS_YOLU, LLM_YOLU], yok=(TAKMA_OR,))
    ih += v561._recete_ihlalleri(r, [(NOUS_YOLU, 2), (LLM_YOLU, 3)], yok=(TAKMA_OR,))
    ih += v557._sizinti(r, kok, log, v561.YENI_NOUS, v561.YENI_OR, ESKI["nous"], ESKI["or"])
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_C5_IKINCI_SIR_surum_kapisinda_duserse_YALNIZ_ilk_yol_yedekli_recetede(tmp_path):
    """LLM yolunun sürümü geçersiz → o yol ne okunur ne yedeklenir; reçete YALNIZ NOUS'un rollback + yedek yolunu taşır."""
    kok, ortam, log, durum = _dunya(tmp_path, SAHTE_METADATA="sifir", SAHTE_METADATA_YOL=LLM_YOLU)
    r = _kos(BETIK, ortam, "--openrouter", "--vault", girdi=f"{v561.YENI_NOUS}\n{v561.YENI_OR}\n")
    ih = v561._iki_sir_ihlalleri(r, log, durum)
    ih += _yedek_ihlalleri(r, kok, "openrouter", [(NOUS_YOLU, ESKI["nous"])], yok=(LLM_YOLU, TAKMA_OR))
    ih += _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "openrouter"), [NOUS_YOLU], yok=(LLM_YOLU, TAKMA_OR))
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_C6_PUT_DUSERSE_yedek_ALINMIS_recete_rollback_ve_yedek_yol(tmp_path):
    """Put düşse bile kasaya ulaşmış OLABİLİR (evre yazımdan ÖNCE `kasa`) — reçete rollback'i VE yedek yolu söyler;
    yedek put'tan ÖNCE alınmıştır."""
    r, kok, _, log, durum = _kos_tenant(tmp_path, SAHTE_PUT_IZIN="0")
    ih = [] if r.returncode == 1 and f"kasaya yazılamadı: {TENANT_YOLU}" in r.stderr else [f"çıkış {r.returncode}"]
    ih += _yedek_ihlalleri(r, kok, "tenant", [(TENANT_YOLU, ESKI["tenant"])])
    ih += _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "tenant"), [TENANT_YOLU])
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def _get_kirik_ihlalleri(r, kok, log, durum) -> list[str]:
    ih = [] if r.returncode == 1 else [f"çıkış {r.returncode} (1 bekleniyordu)"]
    if GET_OKUNAMADI.format(yol=TENANT_YOLU, neden=v561.HICBIR) not in r.stderr.splitlines():
        ih.append("açık hata satırı yok (ESKİ değer kasadan okunamadı … HİÇBİR ŞEY yazılmadı)")
    if v561._putlar(log):
        ih.append(f"kasaya YAZILDI: {v561._putlar(log)}")
    if v561._kasa(durum, TENANT_YOLU) != v561.TOHUM[TENANT_YOLU]:
        ih.append("kasa değişti")
    if v556._restartlar(kok):
        ih.append("birim yeniden başlatıldı")
    rec = v561._recete(r.stderr)
    if not rec or v561.GEREKMEZ not in rec[0]:
        ih.append("reçete 'GEREKMEZ' demiyor (kasaya yazılmadı)")
    if any("kv rollback" in s or s.startswith(YEDEK_ONEKI) for s in rec):
        ih.append("yazılmamış koşumda geri alma adımı önerildi")
    yedek = _yedek_dizini(kok, "tenant")
    if yedek is not None and (yedek / "vault" / TENANT_YOLU).exists():
        ih.append("okunamayan değer için yedek dosyası doğdu")
    return ih


def test_C7_KV_GET_duserse_DURUR_kasaya_YAZIM_YOK_recete_GEREKMEZ(tmp_path):
    """ESKİ değer okunamazsa (sürüm okunduktan sonra — kasa mühürlendi · politika · sürüm silinmiş) yedeksiz bir
    yazım YAPILMAZ: açık hata, put yok, reçete 'GEREKMEZ'."""
    r, kok, _, log, durum = _kos_tenant(tmp_path, SAHTE_GET_KIRIK="1")
    ih = _get_kirik_ihlalleri(r, kok, log, durum)
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_C7b_IKINCI_SIRDA_kv_get_duserse_metin_DOGRU_ilk_yol_recetede(tmp_path):
    """İkinci sırrın ESKİ değeri okunamazsa: hata 'HİÇBİR ŞEY yazılmadı' DEMEZ (ilk sır kasada), put yalnız ilk yol,
    reçete ilk yolun rollback + yedek yolunu taşır, okunamayan yolunkini TAŞIMAZ."""
    kok, ortam, log, durum = _dunya(tmp_path, SAHTE_GET_KIRIK="1", SAHTE_GET_KIRIK_YOL=LLM_YOLU)
    r = _kos(BETIK, ortam, "--openrouter", "--vault", girdi=f"{v561.YENI_NOUS}\n{v561.YENI_OR}\n")
    ih = [] if r.returncode == 1 else [f"çıkış {r.returncode} (1 bekleniyordu)"]
    if GET_OKUNAMADI.format(yol=LLM_YOLU, neden=v561.IKINCI_SIR) not in r.stderr.splitlines():
        ih.append("ikinci sırrın hata satırı 'bu sır YAZILMADI; … ÖNCE yazılan kasa yolu VAR' demiyor")
    if v561.HICBIR in r.stderr:
        ih.append("'HİÇBİR ŞEY yazılmadı' dendi — ilk sır (NOUS) kasada, beyan YALAN")
    if v561._putlar(log) != [NOUS_YOLU]:
        ih.append(f"put yolları {v561._putlar(log)} ≠ [{NOUS_YOLU}]")
    ih += _yedek_ihlalleri(r, kok, "openrouter", [(NOUS_YOLU, ESKI["nous"])], yok=(TAKMA_OR,))
    ih += _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "openrouter"), [NOUS_YOLU], yok=(LLM_YOLU, TAKMA_OR))
    ih += v561._recete_ihlalleri(r, [(NOUS_YOLU, 2)], yok=(LLM_YOLU, TAKMA_OR))
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_C8_DINAMIK_ps_ESKI_ve_YENI_deger_HICBIR_surecin_argvsinde_YOK(tmp_path):
    """v556 deseni: her kv çağrısında ve her `sudo`da süreç tablosu görüntüsü. Görüntüler kv get'in ve yedek yazımının
    argv'sini GÖRÜYOR (pozitif kontrol); ESKİ değer, YENİ değer ve önceki sürüm hiçbir torun sürecin argv'sinde yok."""
    ps = tmp_path / "ps"
    ps.mkdir()
    r, kok, _, log, durum = _kos_tenant(tmp_path, SAHTE_PS_DIZIN=str(ps))
    _iddia(r.returncode == 0, _ozet(r))
    kasa = v561._kasa(durum, TENANT_YOLU)
    ih = _ps_ihlalleri(ps, TENANT_YOLU, ESKI["tenant"], kasa[-1], v561.ONCEKI_TENANT)
    ih += v557._sizinti(r, kok, log, ESKI["tenant"], kasa[-1], v561.ONCEKI_TENANT)
    _iddia(not ih, "\n".join(ih))


# =================================================================================================
# D) YOL YOK / SÜRÜM OKUNAMAZ — sürüm kapısı ÖNCE durdurur, davranış korunur
# =================================================================================================

def _kapi_ihlalleri(r, kok, log, beklenen_hata: str) -> list[str]:
    ih = [] if r.returncode == 1 else [f"çıkış {r.returncode} (1 bekleniyordu)"]
    if beklenen_hata not in r.stderr.splitlines():
        ih.append("sürüm kapısının hata satırı DEĞİŞTİ ya da yok")
    if "ESKİ değer kasadan okunamadı" in r.stderr:
        ih.append("yedek okuması sürüm kapısının ÖNÜNE geçti")
    if any(o.startswith("kv-get") for o in _olaylar(kok)):
        ih.append("sürüm kapısı düşerken kv get yapıldı")
    yedek = _yedek_dizini(kok, "tenant")
    if yedek is not None and (yedek / "vault").exists():
        ih.append("kasa yedeği doğdu")
    if v561._putlar(log):
        ih.append("kasaya YAZILDI")
    rec = v561._recete(r.stderr)
    if not rec or v561.GEREKMEZ not in rec[0] or any(s.startswith(YEDEK_ONEKI) for s in rec):
        ih.append("reçete 'GEREKMEZ' demiyor ya da yedek yol öneriyor")
    return ih


def test_D1_YOL_YOK_ilk_yazim_SURUM_kapisi_DURDURUR_kv_get_ve_yedek_YOK(tmp_path):
    """Kasa yolu hiç yazılmamış (v556 şiminin modeli: current_version 0). Brief: 'bugünkü sürüm kapısı zaten
    durduruyor; davranışı koru' — hata metni v561 D2'ninkiyle AYNI, yedek okuması hiç başlamaz."""
    kok, ortam, log, durum = _dunya(tmp_path)
    veri = json.loads(durum.read_text(encoding="utf-8"))
    del veri[TENANT_YOLU]
    durum.write_text(json.dumps(veri), encoding="utf-8")
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    ih = _kapi_ihlalleri(r, kok, log, v561.GECERSIZ.format(v="0", yol=TENANT_YOLU, neden=v561.HICBIR))
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


def test_D2_SURUM_OKUNAMAZSA_gercek_Vault_yok_cevabi_kv_get_YOK(tmp_path):
    """Gerçek Vault'un yazılmamış yol cevabı (`kv metadata get` 2, stdout boş) — okunamadı kapısı, yedek okuması YOK."""
    kok, ortam, log, durum = _dunya(tmp_path, SAHTE_METADATA="yok")
    r = _kos(BETIK, ortam, "--tenant", "--vault", "--uret")
    ih = _kapi_ihlalleri(r, kok, log, v561.OKUNAMADI.format(yol=TENANT_YOLU, neden=v561.HICBIR))
    _iddia(not ih, "\n".join(ih) + "\n" + _ozet(r))


# =================================================================================================
# E) db/cp BİREBİR — bu dilimin ekleri çıkarılmış betikle İZ KIYASI
# =================================================================================================
# Bu dilim db/cp dallarına DOKUNMAZ; ekler genel döngüde, genel reçetede ve genel kuru rapordadır. İz kıyası bunu
# ölçer: bugünkü betik ile eklerin ÇIKARILDIĞI kopyası AYNI dünyada AYNI senaryoyla koşar (v561 `_iz`: çıkış · stdout
# · stderr · olay sırası · kasa argv'si · dosya durumları). Senaryolar db'nin OTOMATİK yedek yolunu da kapsar.

#: Bu dilimin betiğe EKLEDİĞİ üç metin — taban (E) ve mutasyonlar (M) aynı çapaları kullanır.
YEDEK_BLOK = (
    "    # ESKİ DEĞER YEDEĞİ (TSK-064(b), 2026-09-27) — `--db`/`--cp` dallarının AYNI yöntemi (ayrışma çivisi v567 A1).\n"
    "    # `kv rollback`un KENDİSİ düşerse (politika · ağ · mühür) geri almanın tek girdisi yazım ÖNCESİ KASA değeridir.\n"
    "    # KASADAN okunur, render hedefinden DEĞİL: Agent geride kaldıysa ikisi ayrışır ve doğru olan kasadakidir.\n"
    "    # Sürüm kapısından SONRA: yol yoksa (ilk yazım) o kapı ZATEN durdurur ve hata metni değişmez. Satır + evreden\n"
    "    # ÖNCE: okunamazsa bu yol reçeteye girmez ve kasaya YAZILMAZ (yedeksiz güvence YOK). Değer BASILMAZ, argv'ye\n"
    "    # GİRMEZ: kv get çıktısı 0600 dosyaya yönlenir, `py cikar` yalnız dosya YOLU alır.\n"
    '    ( umask 077; _vault kv get -field=value "$yol" > "$ISLIK/vault_eski_ham" ) \\\n'
    '      || die "ESKİ değer kasadan okunamadı ($yol) — rollback düşerse geri konacak yedek olmadan kasaya YAZILMAZ'
    ' ($yazilmadi)"\n'
    '    sudo install -d -m 0700 -o root -g root "$YEDEK/vault/$(dirname "$yol")"\n'
    '    py cikar dosya "$ISLIK/vault_eski_ham" - - "$YEDEK/vault/$yol"\n'
    '    oldu "yedek: ESKİ değer (KASADAN) → $YEDEK/vault/$yol (0600 — geri almanın girdisi)"\n')
#: TSK-237 (v568): genel reçetenin yedek yol satırı artık ortak yardımcının ÇAĞRISIDIR (satırın biçimi yardımcıda).
RECETE_YEDEK = '          _geri_koy_satiri değer "$yol"\n'
KURU_YEDEK_ECHO = ('    echo "  ESKİ değer yedeği: yedeklenir — kv put ÖNCESİ KASADAN okunur → $KOK/root/sir-yedek-<UTC ts>-'
                   '$alt/vault/$yol (0600); rollback düşerse STDIN\'le: vault kv put $yol value=- (değer BASILMAZ; '
                   'okunamazsa bu yol YAZILMAZ)"\n')
CIKAR_SATIRI = '    py cikar dosya "$ISLIK/vault_eski_ham" - - "$YEDEK/vault/$yol"\n'
INSTALL_SATIRI = '    sudo install -d -m 0700 -o root -g root "$YEDEK/vault/$(dirname "$yol")"\n'
GET_DIE = '      || die "ESKİ değer kasadan okunamadı ($yol)'
PUT_OLDU = '    oldu "kasaya yazıldı: $yol (DEĞER BASILMAZ)"\n'


def _taban_betik(tmp_path: pathlib.Path) -> pathlib.Path:
    return v556._mutant(tmp_path, (YEDEK_BLOK, ""), (RECETE_YEDEK, ""), (KURU_YEDEK_ECHO, ""), ad="taban_v567.sh")


E_SENARYO = (("db_basari", "db", {}, 0, "✓ kasa sürümü (yazım ÖNCESİ): 3"),
             ("db_rollback_kirik", "db", {"SAHTE_ALTER_DUSER": "1", "SAHTE_ROLLBACK_KIRIK": "1"}, 1,
              "YEDEK YOL: ESKİ DSN STDIN'le kv put"),
             ("cp_basari", "cp", {}, 0, "✓ yedek: ESKİ değer (KASADAN) → "),
             ("cp_render_yok", "cp", {"SAHTE_RENDER": "yok"}, 2, YEDEK_ONEKI))


@pytest.mark.parametrize("etiket,dal,bayrak,rc,capa", E_SENARYO, ids=[e[0] for e in E_SENARYO])
def test_E1_DB_CP_bu_dilimin_ekleri_cikarilmis_betikle_BIREBIR_iz(tmp_path, etiket, dal, bayrak, rc, capa):
    """Kıyas boş değil: iki izde de beklenen çıkış kodu ve senaryonun ayırt edici satırı VAR (db: sürüm satırı ·
    OTOMATİK yedek yol; cp: kasa yedeği · reçetenin yedek yol satırı)."""
    taban = _taban_betik(tmp_path)
    a = v561._iz(BETIK, tmp_path / "yeni", dal, bayrak)
    b = v561._iz(taban, tmp_path / "taban", dal, bayrak)
    for k in ("rc", "stdout", "stderr", "olaylar", "kasa_argv", "dosyalar"):
        _iddia(a[k] == b[k], _maskeli(f"{etiket}: {k} ayrıştı\nyeni={a[k]}\ntaban={b[k]}"))
    _iddia(a["rc"] == rc, f"{etiket}: çıkış {a['rc']} ({rc} bekleniyordu)")
    _iddia(capa in a["stdout"] + a["stderr"], _maskeli(f"{etiket}: ayırt edici satır yok\n{a['stdout']}\n{a['stderr']}"))


# =================================================================================================
# M) MUTASYONLAR — mutant tmp'ye yazılır, özgün betik DEĞİŞMEZ
# =================================================================================================

def _mutant(tmp_path: pathlib.Path, ad: str, *ciftler) -> pathlib.Path:
    return v556._mutant(tmp_path, *ciftler, ad=ad)


def test_M1_MUT_YEDEKLEME_kalkarsa_C1_ve_C3_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m1.sh", (YEDEK_BLOK, ""))
    (tmp_path / "c1").mkdir()
    r, kok, _, log, durum = _kos_tenant(tmp_path / "c1", betik=m)
    ih = _tenant_ihlalleri(r, kok, log, durum)
    _iddia(any("yedek dosyası YOK" in i for i in ih) and any("kv get 0 kez" in i for i in ih),
           "MUTASYON ISIRMADI (C1): " + "\n".join(ih))
    (tmp_path / "c3").mkdir()
    r, kok, ortam, _, _ = _kos_tenant(tmp_path / "c3", betik=m, SAHTE_RENDER="yok")
    _iddia("reçetenin gösterdiği yedek dosyası YOK" in _yedek_yolunu_uygula(r, ortam, TENANT_YOLU),
           "MUTASYON ISIRMADI (C3)")


def test_M2_MUT_DEGER_ARGVye_konursa_C1_ve_C8_KIRMIZI(tmp_path):
    """Yedek yazımı değeri bir sürecin ARGV'sine koyar (`sudo <python> -c … "<değer>" <yol>`): statik argv günlüğü
    (sudo şimi) ve dinamik ps görüntüsü İKİSİ de yakalar."""
    argvli = ("    sudo \"$PYTHON_BIN\" -c 'import sys; open(sys.argv[2], \"w\").write(sys.argv[1] + \"\\n\")' "
              "\"$(tr -d '\\r\\n' < \"$ISLIK/vault_eski_ham\")\" \"$YEDEK/vault/$yol\"\n")
    m = _mutant(tmp_path, "m2.sh", (CIKAR_SATIRI, argvli))
    ps = tmp_path / "ps"
    ps.mkdir()
    r, kok, _, log, durum = _kos_tenant(tmp_path, betik=m, SAHTE_PS_DIZIN=str(ps))
    ih = _tenant_ihlalleri(r, kok, log, durum)
    _iddia("değer #1 argv.log içine düştü" in ih, "MUTASYON ISIRMADI (C1 statik): " + "\n".join(ih))
    ih = _ps_ihlalleri(ps, TENANT_YOLU, ESKI["tenant"])
    _iddia(any(i.startswith("değer #0 ") and "süreç argv'sinde" in i for i in ih),
           "MUTASYON ISIRMADI (C8 dinamik): " + "\n".join(ih))


def test_M2b_MUT_RECETE_degeri_ARGVde_gosterirse_C1_ve_C3_KIRMIZI(tmp_path):
    """Reçetenin yedek yol komutu STDIN yerine değeri argv'ye koyar (TSK-237: yardımcının gövdesinde `value="$(tr … <
    yedek)"`) — üç dalın ORTAK satırı olduğu için tek mutasyon üçünü birden bozar."""
    m = _mutant(tmp_path, "m2b.sh", (v568.GOVDE_BORU, v568.GOVDE_ARGV))
    r, kok, ortam, _, _ = _kos_tenant(tmp_path, betik=m, SAHTE_RENDER="yok")
    ih = _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "tenant"), [TENANT_YOLU])
    _iddia(any("STDIN biçiminde değil" in i for i in ih), "MUTASYON ISIRMADI (C1 reçete): " + "\n".join(ih))
    _iddia(any("STDIN biçimli TEK yedek yol satırı yok" in i for i in _yedek_yolunu_uygula(r, ortam, TENANT_YOLU)),
           "MUTASYON ISIRMADI (C3)")


RECETE_KV = v561.RECETE_KV
DOSYADAN_SONRA = ('        while IFS=$\'\\t\' read -r yol surum hedef; do [ -z "$yol" ] || _geri_koy_satiri değer "$yol"; '
                  'done <<< "$GENEL_KASA_SATIRLARI"\n')


@pytest.mark.parametrize("bicim", ["rollbacktan_once", "dosyadan_sonra"])
def test_M3_MUT_RECETE_SIRASI_bozulursa_C1_KIRMIZI(tmp_path, bicim):
    if bicim == "rollbacktan_once":
        m = _mutant(tmp_path, "m3.sh", (RECETE_KV + RECETE_YEDEK, RECETE_YEDEK + RECETE_KV))
        beklenen = "HEMEN ARDINDA değil"
    else:
        m = _mutant(tmp_path, "m3.sh", (RECETE_YEDEK, ""), (v561.RECETE_DOSYA, v561.RECETE_DOSYA + DOSYADAN_SONRA))
        beklenen = "DOSYA adımından SONRA"
    r, kok, _, _, _ = _kos_tenant(tmp_path, betik=m, SAHTE_RENDER="yok")
    ih = _recete_yedek_ihlalleri(r, _yedek_dizini(kok, "tenant"), [TENANT_YOLU])
    _iddia(any(beklenen in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


@pytest.mark.parametrize("bicim", ["dizin_0755", "dosya_0644"])
def test_M4_MUT_YEDEK_IZNI_gevserse_C1_ve_C2_KIRMIZI(tmp_path, bicim):
    if bicim == "dizin_0755":
        m = _mutant(tmp_path, "m4.sh", (INSTALL_SATIRI, INSTALL_SATIRI.replace("-m 0700", "-m 0755")))
    else:
        m = _mutant(tmp_path, "m4.sh", (CIKAR_SATIRI, CIKAR_SATIRI + '    sudo chmod 0644 "$YEDEK/vault/$yol"\n'))
    r, kok, _, log, durum = _kos_tenant(tmp_path, betik=m)
    ih = _tenant_ihlalleri(r, kok, log, durum)
    _iddia(any("izinler" in i for i in ih), "MUTASYON ISIRMADI (C1): " + "\n".join(ih))
    (tmp_path / "cp").mkdir()
    kok_cp, ortam_cp, _, _ = _dunya(tmp_path / "cp")
    _iddia(_kos(BETIK, ortam_cp, "--cp", "--vault").returncode == 0, "emsal koşumu düştü")
    _iddia(_izinler(_yedek_dizini(kok, "tenant"), TENANT_YOLU) != _izinler(_yedek_dizini(kok_cp, "cp"), CP_YOLU),
           "MUTASYON ISIRMADI (C2): izinler emsalle yine aynı")


def test_M5_MUT_KURU_satiri_kalkarsa_B1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m5.sh", (KURU_YEDEK_ECHO, ""))
    kok, ortam, log, _ = _dunya(tmp_path)
    r = _kos(m, ortam, "--tenant", "--vault", "--kuru")
    ih = _kuru_ihlalleri(r, kok, log, "tenant", [TENANT_YOLU])
    _iddia(any("İZLEMİYOR" in i for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M6_MUT_KV_GET_dususu_yutulursa_C7_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, "m6.sh", (GET_DIE, GET_DIE.replace("|| die ", "|| : ", 1)))
    r, kok, _, log, durum = _kos_tenant(tmp_path, betik=m, SAHTE_GET_KIRIK="1")
    ih = _get_kirik_ihlalleri(r, kok, log, durum)
    _iddia(any(i.startswith("kasaya YAZILDI") for i in ih), "MUTASYON ISIRMADI: " + "\n".join(ih))


def test_M7_MUT_YEDEK_put_tan_SONRA_alinirsa_C1_KIRMIZI(tmp_path):
    """Yedek put'tan SONRA alınırsa kasa zaten YENİ değerdedir: yedek geri almanın girdisi olamaz."""
    m = _mutant(tmp_path, "m7.sh", (YEDEK_BLOK, ""), (PUT_OLDU, PUT_OLDU + YEDEK_BLOK))
    r, kok, _, log, durum = _kos_tenant(tmp_path, betik=m)
    ih = _tenant_ihlalleri(r, kok, log, durum)
    _iddia(any("yazım ÖNCESİ kasa değeri DEĞİL" in i for i in ih) and any("put'tan SONRA okundu" in i for i in ih),
           "MUTASYON ISIRMADI: " + "\n".join(ih))

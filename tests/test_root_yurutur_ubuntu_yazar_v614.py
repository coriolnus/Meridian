"""v614 — TSK-265 dilim 1: "ROOT YÜRÜTÜR, UBUNTU YAZAR" sınıf çivisi + tick-watchdog örneği (2026-10-02).

SINIF (Rol-1 A1 ölçümü 2026-10-02 03:0xZ, brief `.superpowers/sdd/tsk265/brief.md`): root olarak koşan
kod, ubuntu'nun YAZABİLDİĞİ bir ağaçtan (`/opt/meridian`, `/opt/hindsight`, `/home/ubuntu` …) yüklenirse
kum havuzundaki (`NoNewPrivileges`) ele geçirilmiş bir ubuntu birimi o dosyayı değiştirip bir sonraki
tetikte ROOT kod yürütür. Kazanılan şey kum havuzu kaçışını kapatmaktır (etkileşimli ubuntu zaten
parolasız sudo taşır). Bu dosya ÖRNEĞİ değil SINIFI ölçer; iki örnek bu dilimde kapandı:

  1. `meridian-tick-watchdog.service` — `User=` yoktu (root), timer'la OTOMATİK koşuyordu,
     `ExecStart=/opt/meridian/deploy/oracle-a1/tick_watchdog.sh`. Rol-1 R1: bekçi `User=ubuntu` koşar,
     tek root gerekçesi (`systemctl restart meridian.service`) DAR polkit kuralına taşınır
     (`52-meridian-tick-watchdog.rules`). Root kodu tamamen kalkar.
  2. `51-meridian-birim-anahtari.rules` — `manage-unit-files` koşulsuz YES. Rol-1 R2 "adlı birimlere
     daralt" dedi; ÖLÇÜM: systemd bu eylemde polkit'e birim adı GEÇİRMEZ (canlı ölçüm 2026-09-02, 51'in
     kendi şerhi). Birim adıyla daraltma polkit katmanında İMKÂNSIZ → kural UYDURULMADI; istisna aşağıda
     BEYANLI, kapanış yolu raporda (API tarafı değişikliği).

BÖLÜMLER
  A. Birimler (depo geneli): root yürütülen her `Exec*` satırı ve o satırın bağlamı
     (`EnvironmentFile`/`Environment`/`WorkingDirectory`/`RootDirectory`/`ExecSearchPath`) ubuntu
     ağacına DOKUNAMAZ. "Root yürütülen" = birim root koşuyorsa (`User=` yok/`root`/`0`, `DynamicUser`
     değil) her `Exec*`; değilse `+`/`!`/`!!` önekli satırlar (systemd bunları `User=`'ı uygulamadan
     yürütür). Brief yalnız `ExecStart*` istedi; `EnvironmentFile` eklendi çünkü root sürece giden ortam
     `LD_PRELOAD` taşıyabilir — aynı sınıf, ölçüm bu kapsamda YENİ bir örnek buldu (hindsight-cp, BEYAN).
  B. Polkit (depo geneli): `manage-units`/`manage-unit-files` veren her `return polkit.Result.YES`
     koruyucu koşullarında POZİTİF bir birim süzgeci taşır (`unit == "…"`, `unit.indexOf("…") == 0`, ya
     da yalnız bunlardan oluşan bir `||`). Eylem kimliği kısıtsız YES iki eylemi de verir sayılır.
  C. Bekçi betiğinde `-I`'sız python yok.
  D. Bekçinin DAVRANIŞI (sahte systemctl, canlıya dokunmaz): FIFO'da asılmaz · bağı izlemez · polkit
     reddinde ADLI satır + sıfırdan farklı çıkış (sessiz başarı yok) · restart parola sormaz.
  E. Örnek: bekçi birimi ubuntu koşar ve yazım izni taşımaz; 52 kuralı statik olarak dar; `node`
     varsa polkit kurallarının TAMAMI (A0 `polkit_kaynaklari` sırasıyla) bir davranış matrisinden geçer.
  F. Pozitif kontrol: sentetik birim/kural/betikle her denetçinin hem öttüğü hem ötmediği hâller.
  H. Beyan hijyeni: beyanlar çürümez, gerekçe ≥20 karakter, kalem kimliği taşır, "kurulmuyor"
     iddiası A0 rolünün kurulum kümesine karşı ÖLÇÜLÜR.
  K. Körlük alarmı: taranan birim/kural/çağrı sayıları ölçülen tabanın ALTINA düşerse kırmızı.

TEK KAYNAK: systemd sözdizimi + drop-in birleştirmesi v553'ten İTHAL edilir (kopya değil). Ubuntu
ağacının türetilen bacağı A0 rolündendir (`repo_kok`, `meridian_kullanici`, `dizinler.yml` sahipleri);
beyanlı bacağı (`/opt/hindsight`) A1 ölçümüyle `UBUNTU_AGACI_BEYANI`ndadır.

MODELLENMEYEN (bilinçli, yanlış-POZİTİF yönünde): polkit'te erken-dönüş negasyonu
(`if (action.id != X) return NOT_HANDLED;` sonrası YES) tanınmaz — kural yazarı pozitif koşul kullanır;
`else` dalı koşulsuz sayılır. Birimlerde `%h` gibi belirteçler çözülmez.

CANLI SİSTEME DOKUNMAZ: SSH yok, `state/` yazımı yok; davranış koşumları `tmp_path` altında sahte
`systemctl` ile. Numara v614: Rol-1 rezervi (ledger 2026-10-02 03:17Z).
"""
from __future__ import annotations

import dataclasses
import json
import os
import posixpath
import re
import shutil
import signal
import subprocess
import datetime as dt
from pathlib import Path

import pytest
import yaml

from tests.test_sertlesmis_birim_yazim_yolu_v553 import (
    _depo_birimleri as _a0_kurulan_birimler,
    _dropinler,
    _yonergeler,
)

KOK = Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy"
ORACLE = DEPLOY / "oracle-a1"
ANSIBLE = DEPLOY / "ansible"
ROL = ANSIBLE / "roles" / "meridian_a1"
DEFAULTS = ROL / "defaults" / "main.yml"
DIZINLER = ROL / "tasks" / "dizinler.yml"
DAGIT_VARS = ANSIBLE / "vars" / "dagit_vars.yml"

WATCHDOG_BIRIM = ORACLE / "meridian-tick-watchdog.service"
WATCHDOG_BETIK = ORACLE / "tick_watchdog.sh"
KURAL_52 = ORACLE / "52-meridian-tick-watchdog.rules"
KURAL_51 = ORACLE / "51-meridian-birim-anahtari.rules"

MU = "org.freedesktop.systemd1.manage-units"
MUF = "org.freedesktop.systemd1.manage-unit-files"
BIRIM_EYLEMLERI = (MU, MUF)

KALEM_DESENI = re.compile(r"^TSK-\d{3}$")

# ================================================================================================
# BEYANLAR — bilinen istisnalar, gerekçe + kalem kimliğiyle (H bölümü çürümelerini ölçer)
# ================================================================================================

#: Ubuntu ağacının A0 rolünün KURMADIĞI ama ubuntu sahipli olduğu ÖLÇÜLEN kökleri.
UBUNTU_AGACI_BEYANI: dict[str, str] = {
    "/opt/hindsight": ("A1 ölçümü (Rol-1, 2026-10-02 03:0xZ, TSK-265 brief): ubuntu:ubuntu 755; A0 rolü "
                       "bu dizini KURMAZ (Hindsight kurulumu elle, deploy/hindsight/)"),
}

#: A bölümünün bilinen ihlalleri. Anahtar depo-göreli birim yolu; `alanlar` ihlali taşıyan yönerge
#: adları (her biri bugün en az bir bulguyu karşılamak ZORUNDA); `kurulu` A0 `birim_kaynaklari`
#: kümesine karşı ölçülür (yanlış "kurulmuyor" iddiası kırmızıdır).
SINIF_BEYANI: dict[str, dict] = {
    "deploy/hindsight/hindsight-cp.service": {
        "alanlar": ("EnvironmentFile",),
        "kurulu": True,
        "kalem": "TSK-265",
        "gerekce": (
            "YENİ BULGU (v614 taraması, 2026-10-02): birim root koşar (docker CLI) ve etkin "
            "EnvironmentFile'ı /opt/hindsight/.env-cp.vault — dizin ubuntu sahipli olduğundan dosya "
            "yerine başkası konabilir; ortam LD_PRELOAD taşırsa root docker sürecine kod yüklenir. "
            "Dilim 1 kapsamı dışı: düzeltme yan dosyanın root sahipli bir dizine (ör. /etc/hindsight/) "
            "taşınmasıdır (vault agent.hcl hedefi + drop-in), Rol-1 kararı."),
    },
    "deploy/meridian.service": {
        "alanlar": ("WorkingDirectory",),
        "kurulu": False,
        "kalem": "TSK-265",
        "gerekce": (
            "ESKİ docker-compose birimi (A1 öncesi kalıntı): root, WorkingDirectory=/opt/meridian, "
            "`docker compose up --build` — compose dosyası root-eşdeğeridir. A0 `birim_kaynaklari` "
            "bu dosyayı KURMAZ (H1 ölçer); kurulum kümesine girdiği gün bu beyan kırmızıya döner."),
    },
}

#: B bölümünün bilinen ihlalleri: (depo-göreli kural yolu, eylem kimliği).
POLKIT_BEYANI: dict[tuple[str, str], dict] = {
    ("deploy/oracle-a1/51-meridian-birim-anahtari.rules", MUF): {
        "kalem": "TSK-265",
        "gerekce": (
            "R2 ölçümü (2026-10-02): systemd manage-unit-files denetiminde polkit'e unit/verb ayrıntısı "
            "GEÇİRMEZ (canlı ölçüm 2026-09-02, kuralın şerhi) — birim adıyla daraltma polkit katmanında "
            "imkânsız, uydurma süzgeç hiç eşleşmez. Tek kullanıcı API birim anahtarı "
            "(`systemctl enable|disable --now`, learn/barsarchive). Kapanış: anahtar enable/disable'dan "
            "vazgeçip yalnız manage-units (birim süzgeçli) kullanır — raporun önerisi, Rol-1 kararı."),
    },
}


# ================================================================================================
# Ortak girdiler
# ================================================================================================

def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _goreli(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(KOK.resolve()))
    except ValueError:
        return str(p)


_BUDA = {"node_modules", "venv", "__pycache__", "state", "backups"}


def _depo_dosyalari(sonek: str) -> list[Path]:
    """Depo ağacındaki `*<sonek>` dosyaları — DOSYA SİSTEMİNDEN (commit'lenmemiş yeni birim de taranır).
    Nokta dizinleri (`.git`, `.venv`, `.claude/worktrees` …) ve üretim/çalışma dizinleri budanır."""
    bulunan: list[Path] = []
    for kok, dizinler, dosyalar in os.walk(KOK):
        dizinler[:] = [d for d in dizinler if not d.startswith(".") and d not in _BUDA]
        bulunan += [Path(kok) / f for f in dosyalar if f.endswith(sonek)]
    return sorted(bulunan)


def _sablon(metin: str, degerler: dict) -> str:
    """`{{ ad }}` → defaults değeri; iç içe şablonlar için birkaç tur. Çözülemeyen yer tutucu kalır."""
    for _ in range(5):
        yeni = re.sub(r"\{\{\s*(\w+)\s*\}\}",
                      lambda m: str(degerler[m.group(1)]) if m.group(1) in degerler else m.group(0), metin)
        if yeni == metin:
            break
        metin = yeni
    return metin


def _ubuntu_agaci() -> dict[str, str]:
    """ubuntu'nun yazabildiği kökler → kaynak. A0 rolünden türeyen bacak + BEYANLI bacak, sonra
    en dar köke indirgenir (bir kökün altındaki kök ayrıca tutulmaz)."""
    d = _defaults()
    kul = d["meridian_kullanici"]
    kokler: dict[str, str] = {
        posixpath.normpath(d["repo_kok"]): "defaults.repo_kok",
        f"/home/{kul}": "defaults.meridian_kullanici ev dizini",
    }
    for g in yaml.safe_load(DIZINLER.read_text(encoding="utf-8")) or []:
        arg = g.get("ansible.builtin.file") or g.get("file")
        if not isinstance(arg, dict) or arg.get("state") != "directory":
            continue
        if _sablon(str(arg.get("owner", "")), d) != kul:
            continue
        yol = _sablon(str(arg.get("path", "")), d)
        if "{{" in yol:                      # döngü değişkeni: çözülebilen öneke indir
            yol = yol[: yol.index("{{")]
        yol = posixpath.normpath(yol) if yol.startswith("/") else ""
        if yol and yol != "/":
            kokler.setdefault(yol, f"dizinler.yml: {g.get('name')}")
    kokler.update(UBUNTU_AGACI_BEYANI)
    dar = {k: v for k, v in kokler.items()
           if not any(k != u and k.startswith(u.rstrip("/") + "/") for u in kokler)}
    return dict(sorted(dar.items()))


def _agac_isabetleri(metin: str, kokler) -> list[str]:
    """Metinde YOL SINIRINDA geçen ubuntu kökleri (`/opt/meridian-eski` `/opt/meridian` DEĞİLDİR;
    `-/opt/x` ve `PYTHONPATH=/opt/x` gibi önekli/atamalı biçimler yakalanır)."""
    bulunan = set()
    for kok in kokler:
        desen = r"(?<![\w./])" + re.escape(kok) + r"(?=$|[/\s'\";:,)\\])"
        if re.search(desen, metin):
            bulunan.add(kok)
    return sorted(bulunan)


# ================================================================================================
# A — birimler: root yürütülen satır + bağlamı ubuntu ağacına dokunamaz
# ================================================================================================

EXEC_ANAHTARLARI = ("ExecCondition", "ExecStartPre", "ExecStart", "ExecStartPost",
                    "ExecReload", "ExecStop", "ExecStopPost")
BAGLAM_LISTE = ("EnvironmentFile", "Environment", "ExecSearchPath")
BAGLAM_SKALER = ("WorkingDirectory", "RootDirectory", "RootImage")


@dataclasses.dataclass
class _Birim:
    yol: Path
    kullanici: str = "root"
    grup: str = ""
    dinamik: bool = False
    exec_: dict = dataclasses.field(default_factory=dict)     # anahtar → [(değer, kaynak)]
    baglam: dict = dataclasses.field(default_factory=dict)    # anahtar → [(değer, kaynak)]
    rwp: list = dataclasses.field(default_factory=list)       # ReadWritePaths girdileri

    @property
    def root_kosar(self) -> bool:
        return self.kullanici in ("root", "0") and not self.dinamik


def _birim_etkin(yol: Path) -> _Birim:
    """Birim + drop-in'ler systemd sırasıyla: liste yönergeleri BİRİKİR ve boş atama SIFIRLAR;
    skalerlerde son yazan kazanır, boş `User=` varsayılana (root) döner."""
    b = _Birim(yol=yol)
    for kaynak in [yol, *_dropinler(yol)]:
        for bolum, anahtar, deger in _yonergeler(kaynak.read_text(encoding="utf-8")):
            if bolum != "Service":
                continue
            if anahtar == "User":
                b.kullanici = deger or "root"
            elif anahtar == "Group":
                b.grup = deger
            elif anahtar == "DynamicUser":
                b.dinamik = deger.strip().lower() in ("yes", "true", "1", "on")
            elif anahtar == "ReadWritePaths":
                b.rwp = [] if not deger else b.rwp + deger.split()
            elif anahtar in EXEC_ANAHTARLARI or anahtar in BAGLAM_LISTE:
                hedef = b.exec_ if anahtar in EXEC_ANAHTARLARI else b.baglam
                if not deger:
                    hedef[anahtar] = []
                else:
                    hedef.setdefault(anahtar, []).append((deger, kaynak))
            elif anahtar in BAGLAM_SKALER:
                b.baglam[anahtar] = [(deger, kaynak)] if deger else []
    return b


def _ayricalikli(deger: str) -> bool:
    """`+`, `!`, `!!` öneki: systemd satırı `User=`/`Group=` UYGULAMADAN yürütür (systemd.service(5))."""
    onek = re.match(r"^[-@:+!]*", deger).group(0)
    return "+" in onek or "!" in onek


def _root_satirlari(b: _Birim) -> list[tuple[str, str, Path]]:
    satirlar = [(a, d, k) for a, liste in b.exec_.items() for d, k in liste
                if b.root_kosar or _ayricalikli(d)]
    if satirlar:   # root yürütülen bir satır varsa birimin bağlamı da o sürece gider
        satirlar += [(a, d, k) for a, liste in b.baglam.items() for d, k in liste]
    return satirlar


def _sinif_bulgulari(birimler: list[Path], kokler) -> tuple[list[dict], int]:
    """Dönüş: (bulgular, root yürüten birim sayısı)."""
    bulgular: list[dict] = []
    root_birim = 0
    for yol in birimler:
        b = _birim_etkin(yol)
        satirlar = _root_satirlari(b)
        if satirlar:
            root_birim += 1
        for alan, deger, kaynak in satirlar:
            isabet = _agac_isabetleri(deger, kokler)
            if isabet:
                bulgular.append({"birim": _goreli(yol), "alan": alan, "deger": deger[:160],
                                 "kaynak": _goreli(kaynak), "kokler": isabet,
                                 "kullanici": b.kullanici})
    return bulgular, root_birim


def _bicimle(bulgular) -> str:
    return "\n".join(f"  · {b}" for b in bulgular)


def test_A1_root_yurutulen_birim_ubuntu_agacina_DOKUNMAZ():
    bulgular, _ = _sinif_bulgulari(_depo_dosyalari(".service"), _ubuntu_agaci())
    beyansiz = [b for b in bulgular
                if b["alan"] not in SINIF_BEYANI.get(b["birim"], {}).get("alanlar", ())]
    assert not beyansiz, (
        "ROOT YÜRÜTÜR, UBUNTU YAZAR — root olarak yürütülen bir satır (ya da bağlamı) ubuntu'nun "
        "yazabildiği ağaca dokunuyor:\n" + _bicimle(beyansiz) + "\n"
        f"ubuntu ağacı: {sorted(_ubuntu_agaci())}\n"
        "ÇARE: birime `User=ubuntu` (root gerekçesi varsa onu DAR bir polkit kuralına taşı — emsal "
        "52-meridian-tick-watchdog.rules) ya da yürütülen dosyayı root sahipli bir yola kur. İstisna "
        "ancak SINIF_BEYANI'na gerekçe + kalem kimliğiyle.")


# ================================================================================================
# B — polkit: birim eylemlerinde YES, pozitif birim süzgeci olmadan verilemez
# ================================================================================================

_JETON = re.compile(r"""
    (?P<bosluk>\s+)
  | (?P<yorum>//[^\n]*|/\*.*?\*/)
  | (?P<dizge>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
  | (?P<ad>[A-Za-z_$][\w$]*)
  | (?P<sayi>\d+(?:\.\d+)?)
  | (?P<isaret>===|!==|==|!=|&&|\|\||<=|>=|[-+*/%<>=!?:;,.(){}\[\]])
""", re.S | re.X)


def _jetonlar(metin: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(metin):
        m = _JETON.match(metin, i)
        if not m:
            raise ValueError(f"polkit kuralı ayrıştırılamadı (konum {i}): {metin[i:i + 40]!r}")
        if m.lastgroup not in ("bosluk", "yorum"):
            out.append(m.group(0))
        i = m.end()
    return out


def _esi(j: list[str], i: int, ac: str, kapa: str) -> int:
    derinlik = 0
    for k in range(i, len(j)):
        if j[k] == ac:
            derinlik += 1
        elif j[k] == kapa:
            derinlik -= 1
            if derinlik == 0:
                return k
    raise ValueError(f"eşleşmeyen {ac}")


def _ust_duzey_bol(j: list[str], ayrac: str) -> list[list[str]]:
    parcalar, simdiki, derinlik = [], [], 0
    for t in j:
        if t in "([{":
            derinlik += 1
        elif t in ")]}":
            derinlik -= 1
        if t == ayrac and derinlik == 0:
            parcalar.append(simdiki)
            simdiki = []
        else:
            simdiki.append(t)
    parcalar.append(simdiki)
    return parcalar


def _soy(j: list[str]) -> list[str]:
    while len(j) >= 2 and j[0] == "(" and _esi(j, 0, "(", ")") == len(j) - 1:
        j = j[1:-1]
    return j


def _dizge(t: str) -> str | None:
    return t[1:-1] if len(t) >= 2 and t[0] in "\"'" and t[-1] == t[0] else None


_ACTION_ID = ["action", ".", "id"]
_LOOKUP_UNIT = [["action", ".", "lookup", "(", '"unit"', ")"],
                ["action", ".", "lookup", "(", "'unit'", ")"]]


def _ayrik_turu(j: list[str], unit_degiskenleri: set[str]):
    """Bir `||` ayrığını sınıflar: ("id", değer) · ("idonek", önek) · ("unit",) · ("diger",)."""
    j = _soy(j)
    esit = ("==", "===")
    # action.id == "X" ya da "X" == action.id
    if len(j) == 5 and j[:3] == _ACTION_ID and j[3] in esit and _dizge(j[4]) is not None:
        return ("id", _dizge(j[4]))
    if len(j) == 5 and j[2:] == _ACTION_ID and j[1] in esit and _dizge(j[0]) is not None:
        return ("id", _dizge(j[0]))
    # action.id.indexOf("P") == 0  |  action.id.startsWith("P")
    if j[:3] == _ACTION_ID and j[3:5] == [".", "indexOf"] and len(j) == 10 and j[5] == "(" \
            and _dizge(j[6]) is not None and j[7] == ")" and j[8] in esit and j[9] == "0":
        return ("idonek", _dizge(j[6]))
    if j[:3] == _ACTION_ID and j[3:5] == [".", "startsWith"] and len(j) == 8 and j[5] == "(" \
            and _dizge(j[6]) is not None and j[7] == ")":
        return ("idonek", _dizge(j[6]))
    # birim ifadesi: action.lookup("unit") ya da ondan atanmış değişken
    def _birim_ifadesi(k: list[str]) -> bool:
        return k in _LOOKUP_UNIT or (len(k) == 1 and k[0] in unit_degiskenleri)
    for i, t in enumerate(j):
        if t in esit and _birim_ifadesi(j[:i]) and len(j) == i + 2 and _dizge(j[i + 1]):
            return ("unit",)
        if t in esit and _birim_ifadesi(j[i + 1:]) and i == 1 and _dizge(j[0]):
            return ("unit",)
    for i in range(len(j)):
        on = j[:i]
        if _birim_ifadesi(on) and j[i:i + 3] == [".", "indexOf", "("] and len(j) == i + 7 \
                and _dizge(j[i + 3]) and j[i + 4] == ")" and j[i + 5] in esit and j[i + 6] == "0":
            return ("unit",)
        if _birim_ifadesi(on) and j[i:i + 3] == [".", "startsWith", "("] and len(j) == i + 5 \
                and _dizge(j[i + 3]) and j[i + 4] == ")":
            return ("unit",)
    return ("diger",)


def _kosul_ozeti(kosullar: list[list[str]], unit_degiskenleri: set[str]) -> dict:
    """Koruyucu koşullar (hepsi VE) → {"id_kisitlari": [[(tür, değer)…]…], "unit_suzgeci": bool,
    "bilesenler": [ayrık türleri listesi]}."""
    id_kisitlari, unit_suzgeci, bilesenler = [], False, []
    for kosul in kosullar:
        for vee in _ust_duzey_bol(_soy(kosul), "&&"):
            ayriklar = [_ayrik_turu(a, unit_degiskenleri) for a in _ust_duzey_bol(_soy(vee), "||")]
            bilesenler.append(ayriklar)
            if all(a[0] in ("id", "idonek") for a in ayriklar):
                id_kisitlari.append(ayriklar)
            if all(a[0] == "unit" for a in ayriklar):
                unit_suzgeci = True
    return {"id_kisitlari": id_kisitlari, "unit_suzgeci": unit_suzgeci, "bilesenler": bilesenler}


def _verir_mi(ozet: dict, eylem: str) -> bool:
    """Bu YES `eylem`i kapsıyor mu? Her id kısıtının en az bir ayrığı eylemi eşlemeli; kısıt yoksa EVET."""
    for ayriklar in ozet["id_kisitlari"]:
        if not any((t == "id" and v == eylem) or (t == "idonek" and eylem.startswith(v))
                   for t, v in ayriklar):
            return False
    return True


def _yes_korumalari(metin: str) -> tuple[list[dict], list[int]]:
    """Her `return polkit.Result.YES` için koruyucu koşul özeti + çözümlenemeyen YES konumları.

    Yürüyüş: `if (k) {` / `if (k) <ifade>;` çerçeve iter; `}` blok çerçevesini, `;` tek-ifade
    çerçevelerini kapatır; `else` koşulsuz çerçevedir (negasyon pozitif süzgeç DEĞİLDİR)."""
    j = _jetonlar(metin)
    unit_degiskenleri: set[str] = set()
    for i in range(len(j) - 7):
        if j[i + 1] == "=" and j[i + 2:i + 8] in _LOOKUP_UNIT and re.fullmatch(r"[A-Za-z_$][\w$]*", j[i]):
            unit_degiskenleri.add(j[i])
    yigin: list[tuple[str, list[str] | None]] = []
    korumalar: list[dict] = []
    cozumsuz: list[int] = []
    i = 0
    while i < len(j):
        t = j[i]
        if t == "if" and i + 1 < len(j) and j[i + 1] == "(":
            k = _esi(j, i + 1, "(", ")")
            kosul = j[i + 2:k]
            if k + 1 < len(j) and j[k + 1] == "{":
                yigin.append(("blok", kosul))
                i = k + 2
            else:
                yigin.append(("tek", kosul))
                i = k + 1
            continue
        if t == "else":
            if i + 1 < len(j) and j[i + 1] == "{":
                yigin.append(("blok", None))
                i += 2
            else:
                yigin.append(("tek", None))
                i += 1
            continue
        if t == "{":
            yigin.append(("blok", None))
        elif t == "}":
            while yigin and yigin[-1][0] == "tek":
                yigin.pop()
            if yigin:
                yigin.pop()
            while yigin and yigin[-1][0] == "tek":
                yigin.pop()
        elif t == ";":
            while yigin and yigin[-1][0] == "tek":
                yigin.pop()
        elif j[i:i + 5] == ["polkit", ".", "Result", ".", "YES"]:
            if i > 0 and j[i - 1] == "return":
                kosullar = [k for _, k in yigin if k is not None]
                ozet = _kosul_ozeti(kosullar, unit_degiskenleri)
                ozet["konum"] = i
                korumalar.append(ozet)
            else:
                cozumsuz.append(i)
            i += 5
            continue
        i += 1
    return korumalar, cozumsuz


def _polkit_bulgulari(kurallar: list[Path]) -> tuple[list[tuple[str, str]], list[str], int]:
    """Dönüş: ((kural, eylem) ihlalleri, çözümlenemeyen-YES iletileri, toplam YES sayısı)."""
    ihlaller: list[tuple[str, str]] = []
    cozumsuz_ileti: list[str] = []
    toplam = 0
    for kural in kurallar:
        korumalar, cozumsuz = _yes_korumalari(kural.read_text(encoding="utf-8"))
        toplam += len(korumalar) + len(cozumsuz)
        for ozet in korumalar:
            for eylem in BIRIM_EYLEMLERI:
                if _verir_mi(ozet, eylem) and not ozet["unit_suzgeci"]:
                    ihlaller.append((_goreli(kural), eylem))
        cozumsuz_ileti += [f"{_goreli(kural)} jeton {c}: `return` dışında polkit.Result.YES — "
                           "koşulu çözümlenemez (tarayıcı kör kalmaz, öter)" for c in cozumsuz]
    return sorted(set(ihlaller)), cozumsuz_ileti, toplam


def test_B1_polkit_birim_eylemlerinde_YES_birim_suzgecsiz_OLAMAZ():
    ihlaller, cozumsuz, _ = _polkit_bulgulari(_depo_dosyalari(".rules"))
    beyansiz = [x for x in ihlaller if x not in POLKIT_BEYANI]
    assert not cozumsuz, "\n".join(cozumsuz)
    assert not beyansiz, (
        "manage-units / manage-unit-files için birim süzgeçsiz `polkit.Result.YES`:\n"
        + "\n".join(f"  · {k} → {e}" for k, e in beyansiz) + "\n"
        "Ele geçirilmiş bir ubuntu servisi DBus'tan `systemctl link /opt/meridian/<kötü>.service` + "
        "`enable` yapabilir; `User=` yoksa birim sonraki açılışta ROOT koşar. ÇARE: pozitif birim "
        "süzgeci (`action.lookup(\"unit\") == \"<ad>\"`); eylem birim ayrıntısı taşımıyorsa YES verme, "
        "POLKIT_BEYANI'na gerekçe + kalem.")


def test_B2_A0_polkit_kaynaklari_taranan_kumede():
    """Tarayıcının gördüğü küme A0'ın KURDUĞU kümeyi kapsamalı — yoksa kurulan bir kural taranmaz."""
    taranan = {p.resolve() for p in _depo_dosyalari(".rules")}
    kurulan = {Path(p.replace("{{ playbook_dir }}", str(ANSIBLE))).resolve()
               for p in _defaults()["polkit_kaynaklari"]}
    assert kurulan, "polkit_kaynaklari boş — kural kurulmuyor ya da liste kayboldu"
    assert kurulan <= taranan, f"taranmayan kurulu kural(lar): {sorted(map(str, kurulan - taranan))}"


# ================================================================================================
# C — bekçi betiğinde izole olmayan python yok
# ================================================================================================

_PYTHON_CAGRISI = re.compile(r"(?<![\w./-])(?:/usr/(?:local/)?bin/)?python[0-9.]*(?![\w.-])(?P<arg>[^\n]*)")


def _python_cagrilari(metin: str) -> list[tuple[str, bool]]:
    """(satır, izole mi) — yorum satırları ölçüm dışı; izole = ilk argüman `-…I…` bayrak kümesi."""
    out = []
    for satir in metin.splitlines():
        if satir.lstrip().startswith("#"):
            continue
        for m in _PYTHON_CAGRISI.finditer(satir):
            ilk = (m.group("arg").split() or [""])[0]
            out.append((satir.strip(), bool(re.fullmatch(r"-[A-Za-z]*I[A-Za-z]*", ilk))))
    return out


def test_C1_bekci_betiginde_python_IZOLE_kosar():
    cagrilar = _python_cagrilari(WATCHDOG_BETIK.read_text(encoding="utf-8"))
    izolesiz = [s for s, izole in cagrilar if not izole]
    assert not izolesiz, (
        "tick_watchdog.sh `-I`'sız python çağırıyor — PYTHONPATH/PYTHONHOME/kullanıcı site-packages ve "
        f"çalışma dizini ithal yoluna girer: {izolesiz}")


# ================================================================================================
# D — bekçinin davranışı (sahte systemctl; canlıya dokunmaz)
# ================================================================================================

_SAHTE_SYSTEMCTL = """#!/bin/sh
# YAS lütfu dalı: 0 = "ölçülemedi" → lütuf atlanır (davranış testi lütfu değil okumayı ölçer)
if [ "$1" = "show" ]; then echo 0; exit 0; fi
echo "$@" >> "__CAGRI__"
__GOVDE__
"""


def _bekci_kos(tmp_path: Path, durum: Path, *, restart_govdesi: str = "exit 0",
               zaman_asimi: float = 20.0) -> tuple[int, str, str, str]:
    """Betiği yeni bir süreç grubunda koşar; zaman aşımında GRUBU öldürür (asılı python torunu
    sızmaz) ve testi düşürür — sonsuz bekleme yok."""
    kutu = tmp_path / "bin"
    kutu.mkdir(exist_ok=True)
    cagri = tmp_path / "systemctl_cagrilari.txt"
    sahte = kutu / "systemctl"
    sahte.write_text(_SAHTE_SYSTEMCTL.replace("__CAGRI__", str(cagri)).replace("__GOVDE__", restart_govdesi))
    sahte.chmod(0o755)
    mono = tmp_path / "uptime"
    mono.write_text("100.00 0.00\n")
    env = {**os.environ,
           "PATH": f"{kutu}:{os.environ.get('PATH', '')}",
           "MERIDIAN_TICK_DURUM": str(durum),
           "MERIDIAN_TICK_MONO_KAYNAK": str(mono),
           "MERIDIAN_TICK_BIRIM": "meridian.service"}
    for ad in ("MERIDIAN_TICK_BAYAT_S", "MERIDIAN_TICK_YAS_LUTUF_S"):
        env.pop(ad, None)
    p = subprocess.Popen(["bash", str(WATCHDOG_BETIK)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.DEVNULL, text=True, env=env, start_new_session=True)
    try:
        out, err = p.communicate(timeout=zaman_asimi)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.communicate()
        pytest.fail(f"bekçi {zaman_asimi:.0f} sn'de bitmedi — okuma ASILDI (süreç grubu öldürüldü). "
                    "Timer'ın oneshot'u hiç bitmez, bekçinin bekçisi yoktur.")
    return p.returncode, out, err, (cagri.read_text() if cagri.exists() else "")


def _bayat_durum(yol: Path) -> Path:
    t = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=10)
    yol.write_text(json.dumps({"updated": t.isoformat(timespec="seconds")}))
    return yol


def test_D1_FIFO_durum_dosyasinda_ASILMAZ_ve_OLCULEMEDI_der(tmp_path):
    fifo = tmp_path / "scheduler_status.json"
    os.mkfifo(fifo)
    rc, out, err, cagrilar = _bekci_kos(tmp_path, fifo)
    assert "ÖLÇÜLEMEDİ" in out, f"FIFO ölçülemeyen hâl olarak adlandırılmadı: out={out!r} err={err!r}"
    # NEDEN de sözleşmedir: yazarsız FIFO bloklamasız okumada BOŞ döner ve JSON hatası da ÖLÇÜLEMEDİ
    # üretir — yalnız sonuca bakan çivi `S_ISREG` kapısının silinmesini görmezdi (mutasyon M11,
    # 2026-10-02). Journal FIFO'yu bozuk JSON'dan AYIRT etmeli; canlı bir yazarın akıttığı FIFO'yu
    # okumaya hiç girmemenin tek kanıtı bu satırdır.
    assert "duzenli dosya degil" in out, f"ÖLÇÜLEMEDİ nedeni FIFO'yu adlandırmıyor: {out!r}"
    assert "restart" not in cagrilar, f"ölçülemeyen okumada restart çağrıldı: {cagrilar!r}"
    assert rc == 0, f"ölçülemeyen hâlin sözleşmesi çıkış 0 (restart YOK): rc={rc} err={err!r}"


def test_D2_bag_durum_dosyasi_IZLENMEZ(tmp_path):
    """Bağın hedefi BAYAT bir düzenli dosya: izlenseydi restart atılırdı. O_NOFOLLOW → ÖLÇÜLEMEDİ."""
    hedef = _bayat_durum(tmp_path / "gercek.json")
    bag = tmp_path / "scheduler_status.json"
    bag.symlink_to(hedef)
    rc, out, err, cagrilar = _bekci_kos(tmp_path, bag)
    assert "ÖLÇÜLEMEDİ" in out, f"bağ izlendi: out={out!r} err={err!r}"
    assert "OSError" in out, f"ÖLÇÜLEMEDİ nedeni bağ reddini (ELOOP) taşımıyor: {out!r}"
    assert "restart" not in cagrilar, f"bağın hedefine bakılıp restart atıldı: {cagrilar!r}"
    assert rc == 0, f"ölçülemeyen hâlin sözleşmesi çıkış 0: rc={rc} err={err!r}"


def test_D3_polkit_reddi_ADLI_satir_ve_SIFIRDAN_FARKLI_cikis(tmp_path):
    """Sessiz başarı yok: `User=ubuntu` bekçide restart yetkisi polkit'tedir; kural kurulu değilse
    systemctl reddeder ve bu journal'da ADIYLA görünmeli, birim `failed` olmalı."""
    durum = _bayat_durum(tmp_path / "scheduler_status.json")
    rc, out, err, cagrilar = _bekci_kos(
        tmp_path, durum,
        restart_govdesi='echo "Failed to restart meridian.service: Interactive authentication required." >&2; exit 1')
    assert "restart" in cagrilar, f"restart hiç denenmedi: {cagrilar!r}"
    assert rc != 0, f"polkit reddinde çıkış 0 — sessiz başarı: out={out!r} err={err!r}"
    birlesik = out + err
    assert "RESTART BAŞARISIZ" in birlesik, f"ret adlandırılmadı: {birlesik!r}"
    assert "Interactive authentication required" in birlesik, "systemctl'in kendi gerekçesi yutuldu"
    assert "52-meridian-tick-watchdog.rules" in birlesik, "ret satırı yetkinin nerede olduğunu söylemiyor"


def test_D4_restart_PAROLA_SORMAZ_ve_basariyi_adlandirir(tmp_path):
    durum = _bayat_durum(tmp_path / "scheduler_status.json")
    rc, out, err, cagrilar = _bekci_kos(tmp_path, durum)
    assert rc == 0, f"başarılı restart'ta çıkış {rc}: err={err!r}"
    assert "--no-ask-password restart meridian.service" in cagrilar, (
        f"restart --no-ask-password taşımıyor (ajansız oturumda yetki sorusu askıda/ belirsiz): {cagrilar!r}")
    assert "yeniden başlatıldı" in out, f"başarı satırı yok: {out!r}"


# ================================================================================================
# E — örnek: bekçi birimi + 52 kuralı
# ================================================================================================

def test_E1_bekci_birimi_ubuntu_kosar_ve_yazim_izni_TASIMAZ():
    b = _birim_etkin(WATCHDOG_BIRIM)
    assert b.kullanici == "ubuntu", f"bekçi birimi etkin kullanıcısı {b.kullanici!r} — root kalmış"
    assert b.grup == "ubuntu", f"bekçi birimi etkin grubu {b.grup!r}"
    assert not b.rwp, f"bekçi diske yazmaz; ReadWritePaths gereksiz yetkidir: {b.rwp}"
    assert not _root_satirlari(b), "bekçide root yürütülen satır kaldı (`+`/`!` öneki?)"
    assert [d for d, _ in b.exec_.get("ExecStart", [])] == ["/opt/meridian/deploy/oracle-a1/tick_watchdog.sh"]


def _tek_yes_bilesenleri(kural: Path) -> list[list[tuple]]:
    korumalar, cozumsuz = _yes_korumalari(kural.read_text(encoding="utf-8"))
    assert not cozumsuz, f"{kural.name}: return dışında YES"
    assert len(korumalar) == 1, f"{kural.name}: TEK YES beklenir, {len(korumalar)} var"
    return korumalar[0]["bilesenler"]


def test_E2_kural_52_TEK_YES_ve_DORT_SART_birden():
    metin = KURAL_52.read_text(encoding="utf-8")
    bilesenler = _tek_yes_bilesenleri(KURAL_52)
    kod = re.sub(r"//[^\n]*", "", metin)
    assert bilesenler.count([("id", MU)]) == 1, f"eylem manage-units'a bağlı değil: {bilesenler}"
    assert [("unit",)] in bilesenler, "birim süzgeci yok"
    assert re.search(r'action\.lookup\("unit"\)\s*==\s*"meridian\.service"', kod), "birim TAM AD değil"
    assert re.search(r'action\.lookup\("verb"\)\s*==\s*"restart"', kod), "fiil `restart`a bağlı değil"
    assert re.search(r'subject\.user\s*==\s*"ubuntu"', kod), "özne ubuntu'ya bağlı değil"
    ayriklar = [a for vee in bilesenler for a in vee]
    assert len(bilesenler) == 4 and all(len(v) == 1 for v in bilesenler), (
        f"52 kuralı tam dört VE-şartı taşımalı (eylem · özne · birim · fiil), `||` yok: {bilesenler}")
    assert not [a for a in ayriklar if a[0] == "idonek"], "eylem önek eşlemesiyle genişletilmiş"


def test_E3_kural_52_A0_rolunde_ve_F9_aynasinda():
    kurulan = [Path(p).name for p in _defaults()["polkit_kaynaklari"]]
    assert KURAL_52.name in kurulan, f"52 kuralı A0 `polkit_kaynaklari`nda yok: {kurulan}"
    f9 = {c["repo"]: c["canli"] for c in yaml.safe_load(DAGIT_VARS.read_text(encoding="utf-8"))["f9_ciftleri"]}
    for kural in (KURAL_51, KURAL_52):
        rel = _goreli(kural)
        assert f9.get(rel) == f"/etc/polkit-1/rules.d/{kural.name}", (
            f"{rel} [F9] içerik aynasında yok — canlıdaki kural depodan ayrışırsa dagit RAPORLAMAZ")


_NODE = shutil.which("node")

_POLKIT_KOSUCU = r"""
const fs = require("fs");
const polkit = {
  Result: {NO: "no", YES: "yes", AUTH_SELF: "auth_self", AUTH_SELF_KEEP: "auth_self_keep",
           AUTH_ADMIN: "auth_admin", AUTH_ADMIN_KEEP: "auth_admin_keep", NOT_HANDLED: null},
  _kurallar: [],
  addRule(f) { this._kurallar.push(f); },
  log() {},
  spawn() { throw new Error("polkit.spawn sınamada YASAK"); },
};
const girdi = JSON.parse(fs.readFileSync(0, "utf8"));
for (const yol of girdi.kurallar) { new Function("polkit", fs.readFileSync(yol, "utf8"))(polkit); }
const sonuc = girdi.vakalar.map(v => {
  const action = {id: v.eylem, lookup: (k) => (Object.prototype.hasOwnProperty.call(v.ayrinti, k) ? v.ayrinti[k] : undefined)};
  const subject = {user: v.ozne, groups: [], local: false, active: false,
                   isInGroup: () => false, isInNetGroup: () => false};
  for (const f of polkit._kurallar) { const r = f(action, subject); if (r) return r; }
  return null;
});
process.stdout.write(JSON.stringify(sonuc));
"""

#: (açıklama, özne, eylem, ayrıntılar, beklenen). `None` = hiçbir kural işlemedi → varsayılan politika
#: (ajansız oturumda RET). "KAYIT" satırları değişmeyen bugünkü davranışı çiviler (onay değildir).
_MATRIS = [
    ("bekçi restart → 52 verir", "ubuntu", MU, {"unit": "meridian.service", "verb": "restart"}, "yes"),
    ("start VERİLMEZ (bekçi yalnız restart çağırır)", "ubuntu", MU, {"unit": "meridian.service", "verb": "start"}, None),
    ("stop VERİLMEZ", "ubuntu", MU, {"unit": "meridian.service", "verb": "stop"}, None),
    ("try-restart VERİLMEZ", "ubuntu", MU, {"unit": "meridian.service", "verb": "try-restart"}, None),
    ("fiil ayrıntısı yoksa VERİLMEZ (fail-closed)", "ubuntu", MU, {"unit": "meridian.service"}, None),
    ("başka özne VERİLMEZ", "nobody", MU, {"unit": "meridian.service", "verb": "restart"}, None),
    ("başka birim VERİLMEZ", "ubuntu", MU, {"unit": "meridian-evil.service", "verb": "restart"}, None),
    ("önek benzeri birim VERİLMEZ", "ubuntu", MU, {"unit": "meridian.service.d", "verb": "restart"}, None),
    ("KAYIT 51: pano anahtarı learn start", "ubuntu", MU, {"unit": "meridian-learn.service", "verb": "start"}, "yes"),
    ("KAYIT 50: sprint örneği start", "ubuntu", MU, {"unit": "meridian-sprint@abc.service", "verb": "start"}, "yes"),
    ("KAYIT 51: manage-unit-files koşulsuz (BEYANLI istisna)", "ubuntu", MUF, {}, "yes"),
    ("KAYIT 51: reload-daemon", "ubuntu", "org.freedesktop.systemd1.reload-daemon", {}, "yes"),
    ("ilgisiz eylem VERİLMEZ", "ubuntu", "org.freedesktop.login1.reboot", {}, None),
    ("set-environment VERİLMEZ", "ubuntu", "org.freedesktop.systemd1.set-environment", {}, None),
]


@pytest.mark.skipif(_NODE is None, reason="node yok — polkit kural DAVRANIŞI ölçülemedi (statik B1/E2 yine koşar)")
def test_E4_polkit_kurallari_DAVRANIS_matrisi_node():
    """Kurallar polkit'in yaptığı gibi koşar: dosyalar AD sırasıyla, kurallar ekleniş sırasıyla, ilk
    `null` olmayan sonuç kazanır; `action.lookup` olmayan ayrıntıya `undefined` döner. Kaynak küme
    A0 `polkit_kaynaklari`dır (canlıya kurulan kümenin TAMAMI)."""
    kurallar = sorted((p.replace("{{ playbook_dir }}", str(ANSIBLE)) for p in _defaults()["polkit_kaynaklari"]),
                      key=lambda p: Path(p).name)
    girdi = {"kurallar": [str(Path(p).resolve()) for p in kurallar],
             "vakalar": [{"ozne": o, "eylem": e, "ayrinti": a} for _, o, e, a, _b in _MATRIS]}
    p = subprocess.run([_NODE, "-e", _POLKIT_KOSUCU], input=json.dumps(girdi), capture_output=True,
                       text=True, timeout=30)
    assert p.returncode == 0, f"node koşucusu düştü: {p.stderr}"
    sonuc = json.loads(p.stdout)
    sapma = [f"{ad}: beklenen {b!r}, gelen {s!r}" for (ad, _o, _e, _a, b), s in zip(_MATRIS, sonuc) if s != b]
    assert not sapma, "polkit davranışı sözleşmeden saptı:\n  " + "\n  ".join(sapma)


# ================================================================================================
# F — pozitif kontrol: denetçiler sentetik girdide hem öter hem susar
# ================================================================================================

_KOKLER = {"/opt/meridian": "t", "/opt/hindsight": "t", "/home/ubuntu": "t"}


def _birim_yaz(tmp_path: Path, ad: str, govde: str, dropinler: dict[str, str] | None = None) -> Path:
    p = tmp_path / ad
    p.write_text(f"[Unit]\nDescription=sentetik\n\n[Service]\n{govde}\n", encoding="utf-8")
    if dropinler:
        d = tmp_path / f"{ad}.d"
        d.mkdir()
        for n, m in dropinler.items():
            (d / n).write_text(m, encoding="utf-8")
    return p


@pytest.mark.parametrize("ad,govde,dropinler,oter", [
    ("root-exec.service", "ExecStart=/opt/meridian/x.sh", None, True),
    ("ubuntu-exec.service", "User=ubuntu\nExecStart=/opt/meridian/x.sh", None, False),
    ("arti-onek.service", "User=ubuntu\nExecStartPre=+/opt/meridian/x.sh\nExecStart=/usr/bin/true", None, True),
    ("unlem-onek.service", "User=ubuntu\nExecStartPost=-!/opt/meridian/x.sh\nExecStart=/usr/bin/true", None, True),
    ("dropin-user-sifirlar.service", "User=ubuntu\nExecStart=/opt/meridian/x.sh",
     {"10.conf": "[Service]\nUser=\n"}, True),
    ("root-envfile.service", "EnvironmentFile=-/opt/hindsight/.env\nExecStart=/usr/bin/docker run x", None, True),
    ("root-docker-temiz.service", "ExecStart=/usr/bin/docker run --rm x", None, False),
    ("exec-sifirlama.service", "ExecStart=/opt/meridian/x.sh",
     {"10.conf": "[Service]\nExecStart=\nExecStart=/usr/bin/true\n"}, False),
    ("onek-benzeri.service", "ExecStart=/opt/meridian-eski/x.sh", None, False),
    ("devam-satiri.service", "ExecStart=/usr/bin/env \\\n  /home/ubuntu/.local/bin/uv run x", None, True),
    ("dinamik.service", "DynamicUser=yes\nExecStart=/opt/meridian/x.sh", None, False),
    ("root-cwd.service", "WorkingDirectory=/opt/meridian\nExecStart=/usr/bin/docker compose up", None, True),
    ("root-ortam.service", "Environment=PATH=/home/ubuntu/.local/bin:/usr/bin\nExecStart=/usr/bin/x", None, True),
    ("yorum-satiri.service", "# ExecStart=/opt/meridian/x.sh\nExecStart=/usr/bin/true", None, False),
])
def test_F1_birim_denetcisi_POZITIF_KONTROL(tmp_path, ad, govde, dropinler, oter):
    birim = _birim_yaz(tmp_path, ad, govde, dropinler)
    bulgular, _ = _sinif_bulgulari([birim], _KOKLER)
    assert bool(bulgular) is oter, f"{ad}: beklenen öter={oter}, bulgular={bulgular}"


@pytest.mark.parametrize("ad,kod,beklenen", [
    ("kosulsuz-muf", 'polkit.addRule(function(a, s){ if (a.id == "x") {} ; '
                     'if (action.id == "org.freedesktop.systemd1.manage-unit-files") { return polkit.Result.YES; } });',
     {MUF}),
    ("eylem-kisitsiz", 'polkit.addRule(function(action, subject){ if (subject.user == "ubuntu") return polkit.Result.YES; });',
     {MU, MUF}),
    ("veya-atlatmasi", 'polkit.addRule(function(action, subject){ var unit = action.lookup("unit"); '
                       'if (action.id == "org.freedesktop.systemd1.manage-units" && '
                       '(unit == "a.service" || subject.user == "ubuntu")) { return polkit.Result.YES; } });',
     {MU}),
    ("negatif-suzgec", 'polkit.addRule(function(action, subject){ var unit = action.lookup("unit"); '
                       'if (action.id == "org.freedesktop.systemd1.manage-units" && unit != "a.service") '
                       '{ return polkit.Result.YES; } });',
     {MU}),
    ("onek-eylem", 'polkit.addRule(function(action, subject){ '
                   'if (action.id.indexOf("org.freedesktop.systemd1.") == 0) { return polkit.Result.YES; } });',
     {MU, MUF}),
    ("else-dali", 'polkit.addRule(function(action, subject){ var unit = action.lookup("unit"); '
                  'if (action.id == "org.freedesktop.systemd1.manage-units") { if (unit == "a.service") '
                  '{ return polkit.Result.NO; } else { return polkit.Result.YES; } } });',
     {MU}),
    ("sprint-deseni-temiz", 'polkit.addRule(function(action, subject){ '
                            'if (action.id == "org.freedesktop.systemd1.manage-units" && subject.user == "ubuntu") {'
                            ' var unit = action.lookup("unit"); if (unit && unit.indexOf("meridian-sprint@") == 0) '
                            '{ return polkit.Result.YES; } } });',
     set()),
    ("veya-iki-birim-temiz", 'polkit.addRule(function(action, subject){ var unit = action.lookup("unit"); '
                             'if (action.id == "org.freedesktop.systemd1.manage-units") { '
                             'if (unit == "a.service" || unit == "b.service") { return polkit.Result.YES; } } });',
     set()),
    ("reload-daemon-kapsam-disi", 'polkit.addRule(function(action, subject){ '
                                  'if (action.id == "org.freedesktop.systemd1.reload-daemon") { return polkit.Result.YES; } });',
     set()),
    ("yorumdaki-yes-sayilmaz", '/* return polkit.Result.YES; */ // return polkit.Result.YES;\n'
                               'polkit.addRule(function(action, subject){ });',
     set()),
    ("tek-ifade-dar-temiz", 'polkit.addRule(function(action, subject){ '
                            'if (action.id == "org.freedesktop.systemd1.manage-units" && '
                            'action.lookup("unit") == "meridian.service") return polkit.Result.YES; '
                            'return polkit.Result.NOT_HANDLED; });',
     set()),
])
def test_F2_polkit_denetcisi_POZITIF_KONTROL(tmp_path, ad, kod, beklenen):
    p = tmp_path / f"{ad}.rules"
    p.write_text(kod, encoding="utf-8")
    ihlaller, cozumsuz, _ = _polkit_bulgulari([p])
    assert not cozumsuz, cozumsuz
    assert {e for _, e in ihlaller} == beklenen, f"{ad}: beklenen {beklenen}, gelen {ihlaller}"


def test_F2b_return_disi_YES_COZUMSUZ_diye_oter(tmp_path):
    p = tmp_path / "degisken.rules"
    p.write_text('polkit.addRule(function(action, subject){ var r = polkit.Result.YES; return r; });')
    _, cozumsuz, _ = _polkit_bulgulari([p])
    assert cozumsuz, "değişkene atanan YES sessizce geçti — tarayıcı kör"


@pytest.mark.parametrize("satir,izole", [
    ('YAS="$(python3 - "$D" <<\'PY\'', False),
    ('YAS="$(python3 -I - "$D" <<\'PY\'', True),
    ("/usr/bin/python3 /opt/x.py", False),
    ("python3 -IS -c 'print(1)'", True),
    ("x=$(python -c 1)", False),
])
def test_F3_python_denetcisi_POZITIF_KONTROL(satir, izole):
    cagrilar = _python_cagrilari(satir)
    assert len(cagrilar) == 1 and cagrilar[0][1] is izole, f"{satir!r} → {cagrilar}"


def test_F3b_yorumdaki_python_olcum_disi():
    assert _python_cagrilari("# python3 - burada anlatılıyor\n  # python3 -c x\n") == []


def test_F4_agac_turetimi_A0_dan_ve_beyandan():
    agac = _ubuntu_agaci()
    for kok in ("/opt/meridian", "/home/ubuntu", "/opt/hindsight", "/opt/veri"):
        assert kok in agac, f"{kok} ubuntu ağacında yok — türetme kırık: {agac}"
    assert "/opt/meridian/var/bots" not in agac, "alt kök ayrıca tutulmuş (en dar küme indirgemesi kırık)"
    assert "/etc/meridian" not in agac, "root sahipli dizin ubuntu ağacına girmiş"


# ================================================================================================
# H — beyan hijyeni
# ================================================================================================

def test_H1_SINIF_BEYANI_curumez_ve_kurulum_iddiasi_OLCULUR():
    bulgular, _ = _sinif_bulgulari(_depo_dosyalari(".service"), _ubuntu_agaci())
    kurulan = {_goreli(p) for p in _a0_kurulan_birimler()}
    sorunlar = []
    for birim, b in SINIF_BEYANI.items():
        for alan in b["alanlar"]:
            if not any(x["birim"] == birim and x["alan"] == alan for x in bulgular):
                sorunlar.append(f"{birim}/{alan}: karşılanan bulgu yok — beyan ÇÜRÜDÜ (sil)")
        if (birim in kurulan) is not b["kurulu"]:
            sorunlar.append(f"{birim}: beyan kurulu={b['kurulu']} ama A0 kümesinde={birim in kurulan}")
        if len(b["gerekce"]) < 20 or not KALEM_DESENI.match(b["kalem"]):
            sorunlar.append(f"{birim}: gerekçe <20 karakter ya da kalem kimliği biçimsiz")
    assert not sorunlar, "\n".join(sorunlar)


def test_H2_POLKIT_BEYANI_curumez():
    ihlaller, _, _ = _polkit_bulgulari(_depo_dosyalari(".rules"))
    sorunlar = [f"{k}: karşılanan ihlal yok — beyan ÇÜRÜDÜ (sil)" for k in POLKIT_BEYANI if k not in ihlaller]
    sorunlar += [f"{k}: gerekçe/kalem eksik" for k, b in POLKIT_BEYANI.items()
                 if len(b["gerekce"]) < 20 or not KALEM_DESENI.match(b["kalem"])]
    assert not sorunlar, "\n".join(sorunlar)


def test_H3_UBUNTU_AGACI_BEYANI_gerekceli():
    for kok, gerekce in UBUNTU_AGACI_BEYANI.items():
        assert kok.startswith("/") and len(gerekce) >= 20, f"{kok}: gerekçe eksik"


# ================================================================================================
# K — körlük alarmı (tabanlar 2026-10-02'de ölçüldü; altına düşmek tarayıcının kör kaldığı demektir)
# ================================================================================================

#: Ölçüm 2026-10-02 (worktree tsk265-root-yolu, dilim 1 uygulandıktan sonra): 35 `.service`; root
#: yürüten 11 (apisix ×2 · hindsight-cp · deploy/meridian.service · telemetri ×3 · vault-admin-yenile ·
#: vault-agent · vault-unseal · vault.service'in `+` önekli ExecStartPost'u); 3 `.rules`, 5
#: `return polkit.Result.YES` (50:1 · 51:3 · 52:1); bekçide 1 python çağrısı.
TABAN_BIRIM = 35
TABAN_ROOT_BIRIM = 11
TABAN_KURAL = 3
TABAN_YES = 5
TABAN_BEKCI_PYTHON = 1


def test_K1_korluk_alarmi_birim_tarayicisi():
    birimler = _depo_dosyalari(".service")
    _, root_birim = _sinif_bulgulari(birimler, _ubuntu_agaci())
    assert len(birimler) >= TABAN_BIRIM, f"taranan birim {len(birimler)} < taban {TABAN_BIRIM} — yürüyüş budanmış"
    assert root_birim >= TABAN_ROOT_BIRIM, (
        f"root yürüten birim {root_birim} < taban {TABAN_ROOT_BIRIM} — ayrıştırma her şeyi ubuntu sanıyor olabilir")
    assert (ORACLE / "meridian.service").resolve() in {p.resolve() for p in birimler}


def test_K2_korluk_alarmi_polkit_ve_python():
    kurallar = _depo_dosyalari(".rules")
    _, _, toplam_yes = _polkit_bulgulari(kurallar)
    assert len(kurallar) >= TABAN_KURAL, f"taranan kural {len(kurallar)} < taban {TABAN_KURAL}"
    assert toplam_yes >= TABAN_YES, f"bulunan YES {toplam_yes} < taban {TABAN_YES} — jetonlayıcı kör"
    assert len(_python_cagrilari(WATCHDOG_BETIK.read_text(encoding="utf-8"))) >= TABAN_BEKCI_PYTHON, \
        "bekçide python çağrısı bulunamadı — desen kör"

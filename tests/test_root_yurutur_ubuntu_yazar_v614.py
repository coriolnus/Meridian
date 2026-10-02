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
  G. (düzeltme turu 1, güvenlik incelemesi C1/I1) ubuntu birimleri: docker grubundan yetki alan her
     birim docker soketini birim DOSYASINDA erişilemez kılar (G1); parolasız sudo taşıyan kullanıcıyla
     koşup yazılabilir ağaçtan yürüten birim NNP'siz olamaz ve NNP'si drop-in'e bırakılamaz (G2/G3);
     h3 `--geri-al` NNP kaybolursa yüksek sesle düşer (G6/G7).
  I2. (düzeltme turu 1) A0: polkit kuralı birimlerden ÖNCE kopyalanır ve polkit birimlerin
     daemon-reload'undan ÖNCE yeniden başlar; saglik.yml 52'yi pkcheck ile müdahalesiz ölçer.
  H. Beyan hijyeni: beyanlar çürümez, gerekçe ≥20 karakter, kalem kimliği taşır, "kurulmuyor"
     iddiası A0 rolünün kurulum kümesine karşı ÖLÇÜLÜR.
  K. Körlük alarmı: taranan birim/kural/çağrı sayıları ölçülen tabanın ALTINA düşerse kırmızı.

DÜZELTME TURU 1 (2026-10-02) KÖR NOKTA KAPANIŞLARI (inceleme M3): A'ya `BindPaths`/`BindReadOnlyPaths`,
std akış dosyaları (`file:`/`append:`/`truncate:` — servis yöneticisi bunları `User=`'dan ÖNCE root olarak
açar, kural her birime uygulanır) ve dünya-yazılabilir kökler (`/tmp`, `/var/tmp`, `/dev/shm`) girdi;
B bir İZİN LİSTESİNE döndü (yalnız manage-units + pozitif birim süzgeci kendiliğinden kabul; set-environment,
policykit.exec, reload-daemon, önekli ya da kısıtsız YES ihlaldir). `LoadCredential` (veri bütünlüğü,
yürütme değil) bilerek dışarıda.

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
        "kalem": "TSK-267",
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

#: B bölümünün bilinen ihlalleri: (depo-göreli kural yolu, eylem kimliği). B bir İZİN LİSTESİDİR
#: (düzeltme turu 1, inceleme M3): YES yalnız "manage-units + pozitif birim süzgeci" için kendiliğinden
#: kabul edilir; başka HER eylemin YES'i burada gerekçe + kalemle durmak zorundadır.
POLKIT_BEYANI: dict[tuple[str, str], dict] = {
    ("deploy/oracle-a1/51-meridian-birim-anahtari.rules", MUF): {
        "kalem": "TSK-266",
        "gerekce": (
            "R2 ölçümü (2026-10-02): systemd manage-unit-files denetiminde polkit'e unit/verb ayrıntısı "
            "GEÇİRMEZ (canlı ölçüm 2026-09-02 + systemd v255 kaynağı) — birim adıyla daraltma polkit "
            "katmanında imkânsız. ŞİDDET (güvenlik incelemesi C2): ANINDA root — ubuntu ağacına yazılan "
            "`User=`'sız bir birim link+enable edilir (`WantedBy=meridian-learn.service`), reload-daemon "
            "YES ile okutulur ve 51'in izinli `start meridian-learn` çağrısı onu Wants= bağımlılığı olarak "
            "ayrı yetki sormadan ROOT başlatır (ya da `add-wants meridian.service` + 52 restart). Tek "
            "meşru kullanıcı API birim anahtarı (`systemctl enable|disable --now`, learn/barsarchive). "
            "Kapanış TSK-266: anahtar root sahipli sabit-komutlu şablon birimlere ya da bayrak dosyası + "
            "start/stop'a geçer, bu iki YES silinir."),
    },
    ("deploy/oracle-a1/51-meridian-birim-anahtari.rules", "org.freedesktop.systemd1.reload-daemon"): {
        "kalem": "TSK-266",
        "gerekce": (
            "Aynı zincirin ikinci halkası (C2): link'lenen birim dosyasını systemd'ye okutur. Ayrıntı "
            "taşımaz (systemd v255: details NULL); tek kullanıcısı `systemctl enable|disable`ın kendi "
            "sonundaki Manager.Reload çağrısı. TSK-266 MUF ile birlikte siler (`--no-reload` ya da şablon)."),
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
# BindPaths/BindReadOnlyPaths (düzeltme turu 1, M3): ubuntu ağacındaki bir yolu root sürecin görüş
# alanına bağlar — yürütülen/okunan şeyi ubuntu belirler.
BAGLAM_LISTE = ("EnvironmentFile", "Environment", "ExecSearchPath", "BindPaths", "BindReadOnlyPaths")
BAGLAM_SKALER = ("WorkingDirectory", "RootDirectory", "RootImage")
# Std akış dosyaları (M3): `file:`/`append:`/`truncate:` yolunu servis yöneticisi `User=`'ı uygulamadan
# ÖNCE açar — yani HER birimde (ubuntu birimi dahil) root, ubuntu'nun yönettiği bir dizindeki bağı izleyip
# keyfi bir dosyayı yaratır/kırpar. Bu yüzden bu kural root koşmaya bağlı DEĞİLDİR.
STD_AKIS_ANAHTARLARI = ("StandardInput", "StandardOutput", "StandardError")
STD_AKIS_ONEKLERI = ("file:", "append:", "truncate:")
# NoNewPrivileges'i İMA eden yönergeler (systemd.exec(5) NoNewPrivileges=; `User=` ubuntu birimi
# CAP_SYS_ADMIN taşımadığı için ima koşulsuz geçerlidir).
NNP_IMA_EDEN = ("SystemCallFilter", "SystemCallArchitectures", "RestrictAddressFamilies",
                "RestrictNamespaces", "PrivateDevices", "ProtectKernelTunables", "ProtectKernelModules",
                "ProtectKernelLogs", "ProtectClock", "MemoryDenyWriteExecute", "RestrictRealtime",
                "RestrictSUIDSGID", "LockPersonality")
_YANLIS = ("", "no", "false", "0", "off")


@dataclasses.dataclass
class _Birim:
    yol: Path
    kullanici: str = "root"
    grup: str = ""
    dinamik: bool = False
    exec_: dict = dataclasses.field(default_factory=dict)     # anahtar → [(değer, kaynak)]
    baglam: dict = dataclasses.field(default_factory=dict)    # anahtar → [(değer, kaynak)]
    rwp: list = dataclasses.field(default_factory=list)       # ReadWritePaths girdileri
    std: dict = dataclasses.field(default_factory=dict)       # StandardX → (değer, kaynak)
    ek_gruplar: list = dataclasses.field(default_factory=list)
    erisilemez: list = dataclasses.field(default_factory=list)          # birleşik InaccessiblePaths
    erisilemez_dosyada: list = dataclasses.field(default_factory=list)  # yalnız birim dosyasınınki
    nnp_izi: dict = dataclasses.field(default_factory=dict)          # birleşik: NNP + ima edenler
    nnp_izi_dosyada: dict = dataclasses.field(default_factory=dict)  # yalnız birim dosyasınınki

    @property
    def root_kosar(self) -> bool:
        return self.kullanici in ("root", "0") and not self.dinamik


def _nnp_etkin(iz: dict, dinamik: bool = False) -> bool:
    if iz.get("NoNewPrivileges", "").strip().lower() in ("yes", "true", "1", "on") or dinamik:
        return True
    return any(iz.get(a, "").strip().lower() not in _YANLIS for a in NNP_IMA_EDEN)


def _birim_etkin(yol: Path) -> _Birim:
    """Birim + drop-in'ler systemd sırasıyla: liste yönergeleri BİRİKİR ve boş atama SIFIRLAR;
    skalerlerde son yazan kazanır, boş `User=` varsayılana (root) döner."""
    b = _Birim(yol=yol)
    for kaynak in [yol, *_dropinler(yol)]:
        dosyada = kaynak == yol
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
            elif anahtar == "SupplementaryGroups":
                b.ek_gruplar = [] if not deger else b.ek_gruplar + deger.split()
            elif anahtar == "InaccessiblePaths":
                b.erisilemez = [] if not deger else b.erisilemez + deger.split()
                if dosyada:
                    b.erisilemez_dosyada = [] if not deger else b.erisilemez_dosyada + deger.split()
            elif anahtar == "NoNewPrivileges" or anahtar in NNP_IMA_EDEN:
                b.nnp_izi[anahtar] = deger
                if dosyada:
                    b.nnp_izi_dosyada[anahtar] = deger
            elif anahtar in STD_AKIS_ANAHTARLARI:
                b.std[anahtar] = (deger, kaynak)
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


def _std_akis_yolu(deger: str) -> str | None:
    for onek in STD_AKIS_ONEKLERI:
        if deger.startswith(onek):
            return deger[len(onek):]
    return None


def _sinif_bulgulari(birimler: list[Path], kokler) -> tuple[list[dict], int]:
    """Dönüş: (bulgular, root yürüten birim sayısı)."""
    bulgular: list[dict] = []
    root_birim = 0
    for yol in birimler:
        b = _birim_etkin(yol)
        satirlar = _root_satirlari(b)
        if satirlar:
            root_birim += 1
        # Std akış dosyaları `User=`'dan BAĞIMSIZ olarak root tarafından açılır (M3).
        satirlar += [(a, d, k) for a, (d, k) in b.std.items() if _std_akis_yolu(d) is not None]
        for alan, deger, kaynak in satirlar:
            isabet = _agac_isabetleri(_std_akis_yolu(deger) or deger, kokler)
            if isabet:
                bulgular.append({"birim": _goreli(yol), "alan": alan, "deger": deger[:160],
                                 "kaynak": _goreli(kaynak), "kokler": isabet,
                                 "kullanici": b.kullanici})
    return bulgular, root_birim


#: Herkesin yazabildiği dizinler (M3) — root yürütmesinin bağlamında ubuntu ağacıyla AYNI sınıftır:
#: oraya bir bağ ya da dosya koymak için ubuntu olmak bile gerekmez.
DUNYA_YAZAR_KOKLER: dict[str, str] = {
    "/tmp": "1777 — herkes yazar (PrivateTmp'siz root birimin görüşü host /tmp'dir)",
    "/var/tmp": "1777 — herkes yazar, açılışlar arası kalıcı",
    "/dev/shm": "1777 tmpfs — herkes yazar",
}


def _yazilabilir_kokler() -> dict[str, str]:
    """A/G sınıflarının taradığı kökler: ubuntu ağacı + dünya-yazılabilir dizinler."""
    return {**_ubuntu_agaci(), **DUNYA_YAZAR_KOKLER}


def _bicimle(bulgular) -> str:
    return "\n".join(f"  · {b}" for b in bulgular)


def test_A1_root_yurutulen_birim_ubuntu_agacina_DOKUNMAZ():
    bulgular, _ = _sinif_bulgulari(_depo_dosyalari(".service"), _yazilabilir_kokler())
    beyansiz = [b for b in bulgular
                if b["alan"] not in SINIF_BEYANI.get(b["birim"], {}).get("alanlar", ())]
    assert not beyansiz, (
        "ROOT YÜRÜTÜR, UBUNTU YAZAR — root olarak yürütülen bir satır (ya da bağlamı) ubuntu'nun "
        "yazabildiği ağaca dokunuyor:\n" + _bicimle(beyansiz) + "\n"
        f"yazılabilir kökler: {sorted(_yazilabilir_kokler())}\n"
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


def _verilen_eylemler(ozet: dict) -> set[str]:
    """Bu YES'in verebildiği eylemler: tam kimlik kümesi; yalnız önek kısıtı varsa `"<önek>*"`;
    eylem kısıtı hiç yoksa `"*"` (her eylem). Çelişkili kısıtlar boş küme verir (YES hiç ateşlenmez)."""
    kisitlar = ozet["id_kisitlari"]
    if not kisitlar:
        return {"*"}
    tamlar = [k for k in kisitlar if all(t == "id" for t, _ in k)]
    if tamlar:
        return {v for _, v in tamlar[0] if _verir_mi(ozet, v)}
    return {f"{v}*" for _, v in kisitlar[0]}


def _polkit_bulgulari(kurallar: list[Path]) -> tuple[list[tuple[str, str]], list[str], int]:
    """Dönüş: ((kural, eylem) ihlalleri, çözümlenemeyen-YES iletileri, toplam YES sayısı).

    İZİN LİSTESİ (düzeltme turu 1, inceleme M3): bir YES yalnız "manage-units + pozitif birim süzgeci"
    ise kendiliğinden kabul edilir. Başka her eylem — manage-unit-files, reload-daemon,
    set-environment (PID 1 ortamına LD_PRELOAD), policykit.exec (pkexec), önekli ya da kısıtsız YES —
    ihlaldir ve ancak POLKIT_BEYANI'nda gerekçe + kalemle durabilir."""
    ihlaller: list[tuple[str, str]] = []
    cozumsuz_ileti: list[str] = []
    toplam = 0
    for kural in kurallar:
        korumalar, cozumsuz = _yes_korumalari(kural.read_text(encoding="utf-8"))
        toplam += len(korumalar) + len(cozumsuz)
        for ozet in korumalar:
            for eylem in _verilen_eylemler(ozet):
                if not (eylem == MU and ozet["unit_suzgeci"]):
                    ihlaller.append((_goreli(kural), eylem))
        cozumsuz_ileti += [f"{_goreli(kural)} jeton {c}: `return` dışında polkit.Result.YES — "
                           "koşulu çözümlenemez (tarayıcı kör kalmaz, öter)" for c in cozumsuz]
    return sorted(set(ihlaller)), cozumsuz_ileti, toplam


def test_B1_polkit_birim_eylemlerinde_YES_birim_suzgecsiz_OLAMAZ():
    ihlaller, cozumsuz, _ = _polkit_bulgulari(_depo_dosyalari(".rules"))
    beyansiz = [x for x in ihlaller if x not in POLKIT_BEYANI]
    assert not cozumsuz, "\n".join(cozumsuz)
    assert not beyansiz, (
        "izin listesi dışı `polkit.Result.YES` (yalnız manage-units + pozitif birim süzgeci kendiliğinden "
        "kabul edilir):\n"
        + "\n".join(f"  · {k} → {e}" for k, e in beyansiz) + "\n"
        "Ele geçirilmiş bir ubuntu servisi DBus'tan `systemctl link /opt/meridian/<kötü>.service` + "
        "`enable` + izinli bir start ile birimi ANINDA root koşturur; set-environment PID 1 ortamına "
        "LD_PRELOAD sokar; policykit.exec pkexec'tir. ÇARE: pozitif birim süzgeci "
        "(`action.lookup(\"unit\") == \"<ad>\"`); eylem birim ayrıntısı taşımıyorsa YES verme, ya da "
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
    assert rc == 4, f"polkit reddinde çıkış {rc} (YETKİ kodu 4 beklenir; 0 = sessiz başarı): err={err!r}"
    birlesik = out + err
    assert "RESTART BAŞARISIZ (YETKİ)" in birlesik, f"ret YETKİ olarak adlandırılmadı: {birlesik!r}"
    assert "Interactive authentication required" in birlesik, "systemctl'in kendi gerekçesi yutuldu"
    assert "52-meridian-tick-watchdog.rules" in birlesik, "ret satırı yetkinin nerede olduğunu söylemiyor"


@pytest.mark.parametrize("ileti", [
    "Failed to restart meridian.service: Access denied",
    "Failed to restart meridian.service: Not authorized",
])
def test_D3b_polkit_reddinin_obur_bicimleri_de_YETKI(tmp_path, ileti):
    durum = _bayat_durum(tmp_path / "scheduler_status.json")
    rc, out, err, _ = _bekci_kos(tmp_path, durum, restart_govdesi=f'echo "{ileti}" >&2; exit 1')
    assert rc == 4 and "RESTART BAŞARISIZ (YETKİ)" in out + err, f"{ileti!r} → rc={rc} {err!r}"


def test_D5_is_arizasi_YETKI_diye_adlandirilmaz(tmp_path):
    """İnceleme M1: birim başlatılamadığında (ExecStart düştü) systemctl de sıfırdan farklı döner ama
    bu bir YETKİ reddi değildir. Satır polkit'i suçlarsa operatör yanlış yeri onarır."""
    durum = _bayat_durum(tmp_path / "scheduler_status.json")
    rc, out, err, _ = _bekci_kos(
        tmp_path, durum,
        restart_govdesi=('echo "Job for meridian.service failed because the control process exited with '
                         'error code." >&2; exit 1'))
    birlesik = out + err
    assert rc == 5, f"iş arızasında çıkış {rc} (İŞ kodu 5 beklenir): {birlesik!r}"
    assert "RESTART BAŞARISIZ (İŞ)" in birlesik, f"iş arızası adlandırılmadı: {birlesik!r}"
    assert "(YETKİ)" not in birlesik and "52-meridian-tick-watchdog.rules" not in birlesik, (
        f"iş arızası polkit kuralına yönlendiriyor (yanlış teşhis): {birlesik!r}")
    assert "control process exited" in birlesik, "systemctl'in kendi gerekçesi yutuldu"


def test_D4_restart_PAROLA_SORMAZ_ve_basariyi_adlandirir(tmp_path):
    durum = _bayat_durum(tmp_path / "scheduler_status.json")
    rc, out, err, cagrilar = _bekci_kos(tmp_path, durum)
    assert rc == 0, f"başarılı restart'ta çıkış {rc}: err={err!r}"
    assert "--no-ask-password restart meridian.service" in cagrilar, (
        f"restart --no-ask-password taşımıyor (ajansız oturumda yetki sorusu askıda/ belirsiz): {cagrilar!r}")
    assert "yeniden başlatıldı" in out, f"başarı satırı yok: {out!r}"


def test_D6_basarili_restartta_systemctl_UYARISI_YUTULMAZ(tmp_path):
    """İnceleme M2 (bedel yasası): eski hâlde systemctl'in uyarıları journal'a düşüyordu; çıktıyı yakalamak
    onları başarıda sessizce atmamalı (ör. "unit file changed on disk" = /etc ile depo ayrışmış)."""
    durum = _bayat_durum(tmp_path / "scheduler_status.json")
    uyari = "Warning: The unit file, source configuration file or drop-ins of meridian.service changed on disk."
    rc, out, err, _ = _bekci_kos(tmp_path, durum, restart_govdesi=f'echo "{uyari}" >&2; exit 0')
    assert rc == 0, f"uyarılı başarıda çıkış {rc}"
    assert uyari in out + err, f"başarılı restart'ın systemctl uyarısı yutuldu: out={out!r} err={err!r}"


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
    # Düzeltme turu 1 (I1): NNP birim DOSYASINDA — drop-in'ler sökülebilir (h3 --geri-al, deploy.sh
    # drop-in kopyalamaz) ve NNP'siz ubuntu bekçisi ubuntu ağacından yürütürken parolasız sudo ile root'tur.
    assert b.nnp_izi_dosyada.get("NoNewPrivileges", "").lower() in ("yes", "true"), (
        f"bekçi biriminin KENDİSİ NoNewPrivileges taşımıyor: {b.nnp_izi_dosyada}")
    # C1: docker soketi birim dosyasında erişilemez.
    assert any(g.lstrip("-+") == "/run/docker.sock" for g in b.erisilemez_dosyada), b.erisilemez_dosyada
    # M1: başarısızlığın etkin okuyucusu — emsal vault-admin-yenile (timer'lı oneshot) ile aynı bağ.
    unit_bolumu = [(a, d) for bol, a, d in _yonergeler(WATCHDOG_BIRIM.read_text(encoding="utf-8")) if bol == "Unit"]
    assert ("OnFailure", "meridian-fail-notify.service") in unit_bolumu, (
        f"bekçinin başarısızlığını okuyan yok (Yasa 6): [Unit] = {unit_bolumu}")


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
    ("51: pano anahtarı learn start", "ubuntu", MU, {"unit": "meridian-learn.service", "verb": "start"}, "yes"),
    ("51: pano anahtarı learn stop", "ubuntu", MU, {"unit": "meridian-learn.service", "verb": "stop"}, "yes"),
    ("51: barsarchive start", "ubuntu", MU, {"unit": "meridian-barsarchive.service", "verb": "start"}, "yes"),
    # M4 (düzeltme turu 1): 51 fiil süzer — anahtarın ve öğrenme düğmesinin istediği yalnız start/stop.
    ("51: learn set-property VERİLMEZ", "ubuntu", MU, {"unit": "meridian-learn.service", "verb": "set-property"}, None),
    ("51: learn kill VERİLMEZ", "ubuntu", MU, {"unit": "meridian-learn.service", "verb": "kill"}, None),
    ("51: learn clean VERİLMEZ", "ubuntu", MU, {"unit": "meridian-learn.service", "verb": "clean"}, None),
    ("51: learn restart VERİLMEZ", "ubuntu", MU, {"unit": "meridian-learn.service", "verb": "restart"}, None),
    ("51: fiil ayrıntısı yoksa VERİLMEZ", "ubuntu", MU, {"unit": "meridian-learn.service"}, None),
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
# G — ubuntu birimleri: docker soketi (C1) ve NoNewPrivileges (I1) — düzeltme turu 1
# ================================================================================================
#
# C1 (güvenlik incelemesi, Rol-1 A1 ölçümü 2026-10-02 04:3xZ): `docker:x:110:ubuntu`, `/run/docker.sock`
# root:docker 660 ve canlı meridian/hindsight-api süreçlerinin Groups satırında 110 VAR. `User=` birimi
# kullanıcının ek gruplarını alır; NNP ve salt-okur kök soket `connect()`ini DURDURMAZ → kum havuzlu her
# ubuntu birimi `POST /containers/create {Privileged, Binds:["/:/host"]}` ile ANINDA root. Grup üyeliği
# operatör kararıdır (TSK-195, dokunulmaz); kapanış birim düzeyinde: `InaccessiblePaths=-/run/docker.sock`
# (`/var/run` → `/run` bağı olduğundan `/var/run/docker.sock`u da kapsar), birim DOSYASINDA.
# I1: `User=ubuntu` birimi NNP'siz koşar ve ubuntu ağacından yürütürse, kum havuzlu bir birimin yazdığı
# kod parolasız sudo ile ROOT olur. NNP drop-in'de durursa sökülebilir → birim DOSYASINDA olmalı.

PAKETLER = ROL / "tasks" / "paketler.yml"
DOCKER_SOKETLERI = ("/run/docker.sock", "/var/run/docker.sock")

#: G1 istisnaları: depo-göreli birim yolu → {"kalem", "gerekce"}. BOŞ (2026-10-02): hiçbir ubuntu birimi
#: docker kullanmıyor (Rol-1 depo taraması; docker'ı yalnız root koşan birimler kullanır).
SOKET_BEYANI: dict[str, dict] = {}
#: G2/G3 istisnaları: aynı biçim. BOŞ (2026-10-02, 22 ubuntu birimi ölçüldü).
NNP_BEYANI: dict[str, dict] = {}


def _docker_kimlikleri() -> set[str]:
    """A0'ın docker grubuna eklediği kullanıcılar — `paketler.yml` `ansible.builtin.user` görevlerinden
    türer (tek kaynak; liste elle yazılmaz)."""
    d = _defaults()
    grup = str(d["docker_grubu"])
    kullanicilar: set[str] = set()
    for g in yaml.safe_load(PAKETLER.read_text(encoding="utf-8")) or []:
        arg = g.get("ansible.builtin.user") or g.get("user")
        if not isinstance(arg, dict):
            continue
        gruplar = [x.strip() for x in _sablon(str(arg.get("groups", "")), d).split(",")]
        if grup in gruplar:
            kullanicilar.add(_sablon(str(arg.get("name", "")), d))
    return kullanicilar


def _soket_bulgulari(birimler: list[Path], kimlikler: set[str], grup: str) -> tuple[list[dict], int]:
    """Docker grubundan yetki alan (root olmayan) her birim, docker soketini birleşik yapılandırmada VE
    birim dosyasının kendisinde erişilemez kılmalı. Dönüş: (bulgular, taranan docker-erişimli birim)."""
    bulgular, sayi = [], 0
    for yol in birimler:
        b = _birim_etkin(yol)
        if b.root_kosar:
            continue   # root her şeye erişir — o sınıf A'dadır
        if not (b.kullanici in kimlikler or b.grup == grup or grup in b.ek_gruplar):
            continue
        sayi += 1
        birlesik = {g.lstrip("-+") for g in b.erisilemez}
        dosyada = {g.lstrip("-+") for g in b.erisilemez_dosyada}
        if not birlesik & set(DOCKER_SOKETLERI):
            bulgular.append({"birim": _goreli(yol), "tur": "soket_erisilebilir", "kullanici": b.kullanici})
        elif not dosyada & set(DOCKER_SOKETLERI):
            bulgular.append({"birim": _goreli(yol), "tur": "yalniz_dropinde", "kullanici": b.kullanici})
    return bulgular, sayi


def _agactan_yurutur(b: _Birim, kokler) -> list[str]:
    return sorted({k for liste in [*b.exec_.values(), *b.baglam.values()] for d, _ in liste
                   for k in _agac_isabetleri(d, kokler)})


def _nnp_bulgulari(birimler: list[Path], kullanicilar: set[str], kokler) -> tuple[list[dict], int]:
    """G2 (birleşik) + G3 (dosyada): parolasız sudo taşıyan kullanıcıyla koşup yazılabilir ağaçtan
    yürüten birim NNP'siz olamaz. Dönüş: (bulgular, taranan birim)."""
    bulgular, sayi = [], 0
    for yol in birimler:
        b = _birim_etkin(yol)
        if b.root_kosar or b.kullanici not in kullanicilar:
            continue
        agac = _agactan_yurutur(b, kokler)
        if not agac:
            continue
        sayi += 1
        if not _nnp_etkin(b.nnp_izi, b.dinamik):
            bulgular.append({"birim": _goreli(yol), "tur": "nnp_yok", "agac": agac})
        elif not _nnp_etkin(b.nnp_izi_dosyada, b.dinamik):
            bulgular.append({"birim": _goreli(yol), "tur": "nnp_yalniz_dropinde", "agac": agac})
    return bulgular, sayi


def _sudo_parolasiz_kullanicilar() -> set[str]:
    """ubuntu etkileşimli kabuğu `NOPASSWD: ALL` taşır (Rol-1 A1 ölçümü 2026-10-02, TSK-265 brief).
    A0 sudoers'ı yönetmez (cloud-init); kimlik `meridian_kullanici`dan türer."""
    return {str(_defaults()["meridian_kullanici"])}


def test_G1_docker_grubu_kimligi_docker_soketine_ERISEMEZ():
    kimlikler = _docker_kimlikleri()
    assert kimlikler, "A0 kimseyi docker grubuna eklemiyor görünüyor — türetme kırık (paketler.yml)"
    bulgular, _ = _soket_bulgulari(_depo_dosyalari(".service"), kimlikler, str(_defaults()["docker_grubu"]))
    beyansiz = [x for x in bulgular if x["birim"] not in SOKET_BEYANI]
    assert not beyansiz, (
        f"docker grubu yetkisi taşıyan ({sorted(kimlikler)}) birim docker soketine erişebilir — kum havuzu "
        "kaçışı + ANINDA root (C1):\n" + _bicimle(beyansiz) + "\n"
        "ÇARE: birim DOSYASINA `InaccessiblePaths=-/run/docker.sock` (drop-in'e değil: sökülebilir).")


def test_G2_G3_ubuntu_birimi_NNPsiz_yazilabilir_agactan_YURUTMEZ():
    bulgular, _ = _nnp_bulgulari(_depo_dosyalari(".service"), _sudo_parolasiz_kullanicilar(),
                                 _yazilabilir_kokler())
    beyansiz = [x for x in bulgular if x["birim"] not in NNP_BEYANI]
    assert not beyansiz, (
        "parolasız sudo taşıyan kullanıcıyla koşan birim yazılabilir ağaçtan NNP'siz yürütüyor (root-eşdeğeri) "
        "ya da NNP'si yalnız sökülebilir bir drop-in'de:\n" + _bicimle(beyansiz) + "\n"
        "ÇARE: birim DOSYASINA `NoNewPrivileges=yes` (ya da onu ima eden bir yönerge).")


def test_G4_fail_notify_NNP_birim_DOSYASINDA():
    """I1'in ikinci örneği: fail-notify de User=ubuntu, NNP'si yalnız drop-in'deydi."""
    b = _birim_etkin(ORACLE / "meridian-fail-notify.service")
    assert b.kullanici == "ubuntu"
    assert b.nnp_izi_dosyada.get("NoNewPrivileges", "").lower() in ("yes", "true"), b.nnp_izi_dosyada


def test_G5_SOKET_ve_NNP_BEYANLARI_curumez():
    sb, _ = _soket_bulgulari(_depo_dosyalari(".service"), _docker_kimlikleri(), str(_defaults()["docker_grubu"]))
    nb, _ = _nnp_bulgulari(_depo_dosyalari(".service"), _sudo_parolasiz_kullanicilar(), _yazilabilir_kokler())
    sorunlar = [f"SOKET_BEYANI {k}: karşılanan bulgu yok" for k in SOKET_BEYANI if k not in {x["birim"] for x in sb}]
    sorunlar += [f"NNP_BEYANI {k}: karşılanan bulgu yok" for k in NNP_BEYANI if k not in {x["birim"] for x in nb}]
    for beyan in (SOKET_BEYANI, NNP_BEYANI):
        sorunlar += [f"{k}: gerekçe/kalem eksik" for k, v in beyan.items()
                     if len(v.get("gerekce", "")) < 20 or not KALEM_DESENI.match(v.get("kalem", ""))]
    assert not sorunlar, "\n".join(sorunlar)


# ---- h3 --geri-al: NNP'yi KORUR (I1) -------------------------------------------------------------

H3_BETIK = ORACLE / "h3_tur2_sertlestir.sh"


def _h3_geri_al(tmp_path: Path, birim: str, nnp_degeri: str) -> tuple[int, str, str, str]:
    """`--geri-al`ı SAHTE sudo/systemctl ile koşar. Sahte sudo HİÇBİR ŞEY YÜRÜTMEZ (yalnız kaydeder) —
    betik /etc'yi hedefler; geliştirme makinesine dokunmamak için gerçek sudo PATH'te asla önce gelmez."""
    kutu = tmp_path / "bin"
    kutu.mkdir(exist_ok=True)
    kayit = tmp_path / "sudo_kaydi.txt"
    (kutu / "sudo").write_text(f'#!/bin/sh\necho "$@" >> "{kayit}"\nexit 0\n')
    (kutu / "systemctl").write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        f'  *NoNewPrivileges*--value*) echo "{nnp_degeri}" ;;\n'
        f'  *--value*NoNewPrivileges*) echo "{nnp_degeri}" ;;\n'
        f'  *) echo "NoNewPrivileges={nnp_degeri}"; echo "SystemCallFilter=" ;;\n'
        "esac\nexit 0\n")
    for f in ("sudo", "systemctl"):
        (kutu / f).chmod(0o755)
    env = {**os.environ, "PATH": f"{kutu}:/usr/bin:/bin"}
    p = subprocess.run(["bash", str(H3_BETIK), "--geri-al", birim], capture_output=True, text=True,
                       env=env, stdin=subprocess.DEVNULL, timeout=30)
    return p.returncode, p.stdout, p.stderr, (kayit.read_text() if kayit.exists() else "")


@pytest.mark.parametrize("birim", ["meridian-tick-watchdog", "meridian-fail-notify"])
def test_G6_h3_geri_al_NNP_KORUNDUysa_gecer(tmp_path, birim):
    rc, out, err, sudo = _h3_geri_al(tmp_path, birim, "yes")
    assert f"rm -f /etc/systemd/system/{birim}.service.d/" in sudo, f"sahte sudo kullanılmadı: {sudo!r}"
    assert rc == 0, f"NNP korunduğu hâlde geri alma düştü: {err!r}"
    assert "NoNewPrivileges=yes korundu" in out, out


@pytest.mark.parametrize("birim", ["meridian-tick-watchdog", "meridian-fail-notify"])
def test_G7_h3_geri_al_NNP_KAYBOLURSA_YUKSEK_SESLE_duser(tmp_path, birim):
    rc, out, err, sudo = _h3_geri_al(tmp_path, birim, "no")
    assert f"rm -f /etc/systemd/system/{birim}.service.d/" in sudo, f"sahte sudo kullanılmadı: {sudo!r}"
    assert rc != 0, f"NNP kaybolduğu hâlde geri alma 0 döndü (sessiz root-eşdeğeri): out={out!r}"
    assert "ROOT-EŞDEĞERİ" in err, f"neden adlandırılmadı: {err!r}"


# ================================================================================================
# I2 — A0 sırası: polkit kuralı yeni birimden ÖNCE yürürlüğe girer + saglik.yml pkcheck kapısı
# ================================================================================================

ROL_TASKS = ROL / "tasks"


def _rol_akisi() -> list[tuple[str, dict]]:
    """main.yml'nin import sırasıyla düzleştirilmiş görev akışı: [(dosya, görev)]."""
    akis = []
    for imp in yaml.safe_load((ROL_TASKS / "main.yml").read_text(encoding="utf-8")):
        ad = imp["ansible.builtin.import_tasks"]
        akis += [(ad, g) for g in yaml.safe_load((ROL_TASKS / ad).read_text(encoding="utf-8")) or []]
    return akis


def test_I2a_polkit_kurali_birimlerden_ONCE_yururluge_girer():
    """İnceleme I2: birimler daemon-reload'u kendi flush'ıyla HEMEN yapar; polkit sonra koşuyordu ve
    aradaki bir assert düşerse (sir_denetimi) `User=ubuntu` bekçi kuralsız kalır — "ilerleme var" basar,
    ilk gerçek ihtiyaçta RESTART BAŞARISIZ. Sözleşme: polkit kopyası + polkit restart (flush) birim
    kopyasından ÖNCE. Kural tek başına zararsızdır (yalnız ek yetki)."""
    akis = _rol_akisi()
    polkit_kopya = next(i for i, (ad, g) in enumerate(akis)
                        if "ansible.builtin.copy" in g and "polkit_kaynaklari" in str(g.get("loop", "")))
    birim_kopya = next(i for i, (ad, g) in enumerate(akis)
                       if "ansible.builtin.copy" in g and "birim_kaynaklari" in str(g.get("with_fileglob", "")))
    flushlar = [i for i, (ad, g) in enumerate(akis) if g.get("ansible.builtin.meta") == "flush_handlers"]
    assert polkit_kopya < birim_kopya, (
        f"polkit kuralı birim dosyalarından SONRA kopyalanıyor (akış {polkit_kopya} > {birim_kopya})")
    assert any(polkit_kopya < f < birim_kopya for f in flushlar), (
        "polkit kopyası ile birim kopyası arasında flush_handlers yok — polkit restart'ı birimin "
        "daemon-reload'undan SONRA kalır (handler'lar tanım sırasıyla koşar: önce daemon-reload)")
    assert akis[polkit_kopya][1].get("notify") == "polkit-yeniden-baslat"


def _saglik() -> list[dict]:
    return yaml.safe_load((ROL_TASKS / "saglik.yml").read_text(encoding="utf-8"))


def test_I2b_saglik_pkcheck_kapisi_52yi_ubuntu_oznesiyle_OLCER():
    gorevler = _saglik()
    pk = [g for g in gorevler if "pkcheck" in str(g.get("ansible.builtin.command", ""))]
    assert len(pk) == 1, f"saglik.yml'de tek pkcheck ölçümü beklenir, bulunan {len(pk)}"
    argv = [str(a) for a in pk[0]["ansible.builtin.command"]["argv"]]
    metin = " ".join(argv)
    for parca in ("--action-id org.freedesktop.systemd1.manage-units", "--detail unit meridian.service",
                  "--detail verb restart", "--process"):
        assert parca in metin, f"pkcheck argv'de `{parca}` yok: {argv}"
    fw = str(pk[0].get("failed_when", ""))
    assert "rc" in fw and "not in" in fw and "127" in fw, f"failed_when rc tabanlı değil / 127 yok: {fw!r}"
    assert pk[0].get("changed_when") is False
    ozne = [g for g in gorevler if "pgrep" in str(g.get("ansible.builtin.command", ""))]
    assert ozne and "meridian_kullanici" in str(ozne[0]["ansible.builtin.command"]), (
        "pkcheck öznesi ubuntu sürecinden türemiyor")
    kapi = [g for g in gorevler if "ansible.builtin.assert" in g and "pkcheck_sonuc" in str(g)]
    assert len(kapi) == 1, "pkcheck sonucu bir KAPIYA bağlanmamış"
    assert "pkcheck_sonuc.rc == 0" in str(kapi[0]["ansible.builtin.assert"]["that"])
    olculemedi = [g for g in gorevler if "ansible.builtin.debug" in g and "pkcheck" in str(g.get("when", ""))]
    assert len(olculemedi) == 1, "pkcheck ölçülemediğinde (ikili yok / özne yok / 127 / check-mode) sessiz kalıyor"
    # Rapor DÖRT ölçülemeyen hâlin HER BİRİNDE basılmalı — biri düşerse o hâl "geçti" gibi sessiz geçer
    # (mutasyon F16, 2026-10-02: görev adında ÖLÇÜLEMEDİ geçtiği için ilk sürüm hâlleri ölçmüyordu).
    kosul = re.sub(r"\s+", " ", str(olculemedi[0]["when"]))
    for hal in ("ansible_check_mode", "pkcheck_ikili.stat.exists", "pkcheck_ozne.rc", "pkcheck_sonuc.rc | default(-1)) == 127"):
        assert hal in kosul, f"ÖLÇÜLEMEDİ raporu `{hal}` hâlinde basılmıyor: when = {kosul!r}"
    mesaj = str(olculemedi[0]["ansible.builtin.debug"]["msg"])
    assert "ÖLÇÜLEMEDİ" in mesaj and "HÜKMÜ DEĞİLDİR" in mesaj, f"rapor ölçülemediğini adlandırmıyor: {mesaj!r}"


def test_I2c_deploy_sh_YETKI_ve_IS_arizasini_ayirir():
    d = (ORACLE / "deploy.sh").read_text(encoding="utf-8")
    assert '*"RESTART BAŞARISIZ (YETKİ)"*)' in d and '*"RESTART BAŞARISIZ (İŞ)"*)' in d, (
        "deploy.sh test-ateşleme kapısı YETKİ ile İŞ arızasını ayırmıyor")


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
    # M3 (düzeltme turu 1) kör noktaları:
    ("root-bindpaths.service", "BindReadOnlyPaths=/opt/meridian/x:/etc/x\nExecStart=/usr/bin/true", None, True),
    ("root-tmp-yurutme.service", "ExecStart=/tmp/x.sh", None, True),
    ("root-devshm.service", "ExecStart=/usr/bin/env /dev/shm/x", None, True),
    ("root-vartmp-olmayan.service", "ExecStart=/usr/bin/true /var/tmpx", None, False),
    ("ubuntu-stdout-file.service", "User=ubuntu\nExecStart=/usr/bin/true\nStandardOutput=append:/opt/meridian/x.log",
     None, True),
    ("ubuntu-stderr-truncate-tmp.service", "User=ubuntu\nExecStart=/usr/bin/true\nStandardError=truncate:/tmp/x",
     None, True),
    ("ubuntu-stdout-journal.service", "User=ubuntu\nExecStart=/usr/bin/true\nStandardOutput=journal", None, False),
    ("ubuntu-stdin-file.service", "User=ubuntu\nExecStart=/usr/bin/true\nStandardInput=file:/home/ubuntu/girdi",
     None, True),
])
def test_F1_birim_denetcisi_POZITIF_KONTROL(tmp_path, ad, govde, dropinler, oter):
    birim = _birim_yaz(tmp_path, ad, govde, dropinler)
    bulgular, _ = _sinif_bulgulari([birim], {**_KOKLER, **DUNYA_YAZAR_KOKLER})
    assert bool(bulgular) is oter, f"{ad}: beklenen öter={oter}, bulgular={bulgular}"


@pytest.mark.parametrize("ad,govde,dropinler,beklenen", [
    ("ubuntu-soketsiz.service", "User=ubuntu\nExecStart=/usr/bin/true", None, "soket_erisilebilir"),
    ("ubuntu-soketli.service", "User=ubuntu\nInaccessiblePaths=-/run/docker.sock\nExecStart=/usr/bin/true",
     None, None),
    ("ubuntu-varrun.service", "User=ubuntu\nInaccessiblePaths=-/var/run/docker.sock\nExecStart=/usr/bin/true",
     None, None),
    ("ubuntu-yalniz-dropin.service", "User=ubuntu\nExecStart=/usr/bin/true",
     {"10.conf": "[Service]\nInaccessiblePaths=-/run/docker.sock\n"}, "yalniz_dropinde"),
    ("ubuntu-dropin-sifirlar.service", "User=ubuntu\nInaccessiblePaths=-/run/docker.sock\nExecStart=/usr/bin/true",
     {"10.conf": "[Service]\nInaccessiblePaths=\n"}, "soket_erisilebilir"),
    ("ubuntu-baska-yol.service", "User=ubuntu\nInaccessiblePaths=-/run/containerd/x.sock\nExecStart=/usr/bin/true",
     None, "soket_erisilebilir"),
    ("baska-kullanici-ek-grup.service", "User=nobody\nSupplementaryGroups=docker\nExecStart=/usr/bin/true",
     None, "soket_erisilebilir"),
    ("baska-kullanici.service", "User=nobody\nExecStart=/usr/bin/true", None, None),
    ("root.service", "ExecStart=/usr/bin/true", None, None),
])
def test_F5_soket_denetcisi_POZITIF_KONTROL(tmp_path, ad, govde, dropinler, beklenen):
    birim = _birim_yaz(tmp_path, ad, govde, dropinler)
    bulgular, _ = _soket_bulgulari([birim], {"ubuntu"}, "docker")
    gelen = bulgular[0]["tur"] if bulgular else None
    assert gelen == beklenen, f"{ad}: beklenen {beklenen}, gelen {bulgular}"


@pytest.mark.parametrize("ad,govde,dropinler,beklenen", [
    ("nnp-yok.service", "User=ubuntu\nExecStart=/opt/meridian/x.sh", None, "nnp_yok"),
    ("nnp-dosyada.service", "User=ubuntu\nNoNewPrivileges=yes\nExecStart=/opt/meridian/x.sh", None, None),
    ("nnp-ima-dosyada.service", "User=ubuntu\nSystemCallFilter=@system-service\nExecStart=/opt/meridian/x.sh",
     None, None),
    ("nnp-yalniz-dropin.service", "User=ubuntu\nExecStart=/opt/meridian/x.sh",
     {"10.conf": "[Service]\nNoNewPrivileges=true\n"}, "nnp_yalniz_dropinde"),
    ("nnp-no.service", "User=ubuntu\nNoNewPrivileges=no\nExecStart=/opt/meridian/x.sh", None, "nnp_yok"),
    ("nnp-ima-no.service", "User=ubuntu\nPrivateDevices=no\nExecStart=/opt/meridian/x.sh", None, "nnp_yok"),
    ("agac-disi.service", "User=ubuntu\nExecStart=/usr/bin/true", None, None),
    ("agac-cwd.service", "User=ubuntu\nWorkingDirectory=/opt/meridian\nExecStart=/usr/bin/python3 -m x", None,
     "nnp_yok"),
    ("baska-kullanici.service", "User=nobody\nExecStart=/opt/meridian/x.sh", None, None),
])
def test_F6_NNP_denetcisi_POZITIF_KONTROL(tmp_path, ad, govde, dropinler, beklenen):
    birim = _birim_yaz(tmp_path, ad, govde, dropinler)
    bulgular, _ = _nnp_bulgulari([birim], {"ubuntu"}, _KOKLER)
    gelen = bulgular[0]["tur"] if bulgular else None
    assert gelen == beklenen, f"{ad}: beklenen {beklenen}, gelen {bulgular}"


@pytest.mark.parametrize("ad,kod,beklenen", [
    ("kosulsuz-muf", 'polkit.addRule(function(a, s){ if (a.id == "x") {} ; '
                     'if (action.id == "org.freedesktop.systemd1.manage-unit-files") { return polkit.Result.YES; } });',
     {MUF}),
    ("eylem-kisitsiz", 'polkit.addRule(function(action, subject){ if (subject.user == "ubuntu") return polkit.Result.YES; });',
     {"*"}),
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
     {"org.freedesktop.systemd1.*"}),
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
    # İzin listesi (düzeltme turu 1): reload-daemon artık kendiliğinden kabul EDİLMEZ (C2 zincirinin halkası).
    ("reload-daemon-artik-ihlal", 'polkit.addRule(function(action, subject){ '
                                  'if (action.id == "org.freedesktop.systemd1.reload-daemon") { return polkit.Result.YES; } });',
     {"org.freedesktop.systemd1.reload-daemon"}),
    ("set-environment", 'polkit.addRule(function(action, subject){ if (subject.user == "ubuntu" && '
                        'action.id == "org.freedesktop.systemd1.set-environment") { return polkit.Result.YES; } });',
     {"org.freedesktop.systemd1.set-environment"}),
    ("pkexec", 'polkit.addRule(function(action, subject){ '
               'if (action.id == "org.freedesktop.policykit.exec") { return polkit.Result.YES; } });',
     {"org.freedesktop.policykit.exec"}),
    ("mu-muf-veya-birim-suzgecli", 'polkit.addRule(function(action, subject){ '
                                   'if ((action.id == "org.freedesktop.systemd1.manage-units" || '
                                   'action.id == "org.freedesktop.systemd1.manage-unit-files") && '
                                   'action.lookup("unit") == "a.service") { return polkit.Result.YES; } });',
     {MUF}),
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
    bulgular, _ = _sinif_bulgulari(_depo_dosyalari(".service"), _yazilabilir_kokler())
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
    _, root_birim = _sinif_bulgulari(birimler, _yazilabilir_kokler())
    assert len(birimler) >= TABAN_BIRIM, f"taranan birim {len(birimler)} < taban {TABAN_BIRIM} — yürüyüş budanmış"
    assert root_birim >= TABAN_ROOT_BIRIM, (
        f"root yürüten birim {root_birim} < taban {TABAN_ROOT_BIRIM} — ayrıştırma her şeyi ubuntu sanıyor olabilir")
    assert (ORACLE / "meridian.service").resolve() in {p.resolve() for p in birimler}


#: Ölçüm 2026-10-02 (düzeltme turu 1): docker grubundan yetki alan (User=ubuntu) birim 22; bunların
#: yazılabilir ağaçtan yürüten 22'si NNP taramasına girer.
TABAN_DOCKER_BIRIM = 22
TABAN_NNP_BIRIM = 22


def test_K3_korluk_alarmi_G_tarayicilari():
    birimler = _depo_dosyalari(".service")
    _, soket_sayi = _soket_bulgulari(birimler, _docker_kimlikleri(), str(_defaults()["docker_grubu"]))
    _, nnp_sayi = _nnp_bulgulari(birimler, _sudo_parolasiz_kullanicilar(), _yazilabilir_kokler())
    assert soket_sayi >= TABAN_DOCKER_BIRIM, (
        f"docker-erişimli birim {soket_sayi} < taban {TABAN_DOCKER_BIRIM} — kimlik türetmesi/ayrıştırma kör")
    assert nnp_sayi >= TABAN_NNP_BIRIM, f"NNP taraması {nnp_sayi} < taban {TABAN_NNP_BIRIM} — kör"


def test_K2_korluk_alarmi_polkit_ve_python():
    kurallar = _depo_dosyalari(".rules")
    _, _, toplam_yes = _polkit_bulgulari(kurallar)
    assert len(kurallar) >= TABAN_KURAL, f"taranan kural {len(kurallar)} < taban {TABAN_KURAL}"
    assert toplam_yes >= TABAN_YES, f"bulunan YES {toplam_yes} < taban {TABAN_YES} — jetonlayıcı kör"
    assert len(_python_cagrilari(WATCHDOG_BETIK.read_text(encoding="utf-8"))) >= TABAN_BEKCI_PYTHON, \
        "bekçide python çağrısı bulunamadı — desen kör"

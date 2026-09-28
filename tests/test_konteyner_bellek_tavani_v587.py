"""v587 — TSK-247: docker birimlerinde KONTEYNER bellek tavanı (`--memory`) = birimin `MemoryMax`ı (2026-09-28);
TSK-247(b): CPU eşi — `CPUQuota` beyan eden birimde konteyner CPU tavanı (`--cpus`) = `CPUQuota`/100 (E bölümü).

OLAY (Rol-1 A1 ölçümü, 2026-09-28, salt-okur): `docker inspect` `HostConfig.Memory` = 0 — apisix-kapi, apisix-etcd,
hindsight-cp. Üç konteynerin bellek tavanı makinenin tamamıydı (23,41 GiB). Birimlerdeki `MemoryMax=` (512M / 256M /
512M) YALNIZ `docker run` İSTEMCİ sürecini sınırlıyordu (MemoryCurrent ~9–12 MB): konteyner dockerd'nin cgroup'unda
koşar, birimin cgroup'unda DEĞİL. Kullanım aynı ölçümde: apisix-kapi 89 MiB · apisix-etcd 13 MiB · hindsight-cp 43 MiB.
Emsal: TSK-020 UYGULA-9 Faz A telemetri birimleri iki katmanı ZATEN taşıyordu (`--memory` + `MemoryMax`, v584 A1) —
ama o çivi yalnız kendi üç birimini ölçer; üç eski birim sınıfın dışında kalmıştı (sınıf bir örnekle kapanmaz).

KURAL (A). A0 rolünün KURDUĞU her `.service` biriminde bir komut yönergesi (`KOMUT_YONERGELERI`, v554'ten) `docker run`
(ya da `docker container run`) koşuyorsa:
  · `--memory` TAM BİR kez bulunur (eşdeğer yazımlar: `--memory X`, `-m X`, `-m=X`, `-mX`; `--memory-swap` vb. SAYILMAZ);
  · birimin `MemoryMax=`ı SONLU bir bayt değeridir — yok, boş atamayla sıfırlanmış, `infinity`, yüzde ya da systemd'nin
    tanımadığı küçük harf son ek (`256m`: systemd satırı UYARIYLA yok sayar) → bulgu;
  · ikisi BAYT olarak eşittir (`512m` ↔ `512M`; docker ve systemd ikisi de 1024 tabanlı).
Seçenek ayrıştırması v584'ün `_docker_run`ındadır (tek kaynak). O ayrıştırıcı tanımadığı bayrağı DEĞERSİZ sayar: yanlış
sınıflanan değerli bir bayrak imaj jetonunu kaydırır, `--memory` kapsayıcı argümanlarına düşer ve GÖRÜNMEZ olur — çivi
KIRMIZI (güvenli yön); ters yön (kapsayıcı argümanındaki bir `--memory`nin docker seçeneği sayılması) yapısal olarak
yoktur. Kaymanın kendisi de ADIYLA öter: imaj jetonu etiket/özet taşımıyorsa bulgu (`imaj_jetonu_supheli`, B).

İKİ GÖRÜNÜM. (1) `birim`: dosya tek başına — drop-in yokken ve drop-in'in GERİ ALIM yolunda (apisix drop-in şerhi:
"bu dosyayı kaldır") koşan hâl. (2) `birlesik`: birim + `<ad>.service.d/*.conf` systemd sırasıyla — A0 rolünün A1'e
kurduğu hâl. Komut yönergesinde boş atama listeyi SIFIRLAR (drop-in'in `ExecStart=` + yeniden yazımı), `MemoryMax`
skalerdir (son yazan kazanır; boş atama varsayılana, yani SINIRSIZA döner). apisix'in `50-vault-yan-dosya.conf`u
ExecStart'ı yeniden yazdığı için bayrak orada da durur: iki kopyanın jeton eşitliğini
`tests/test_vault_dalga2_v491.py` C6 ölçer, BİRLEŞİK hâlin tavanını bu dosya.

KAPSAM TEK KAYNAKTAN. Birimler `defaults/main.yml::birim_kaynaklari` glob'larından türer (v553 `_depo_birimleri`
deseni; türetimin v553 ile eşitliği A0'da çivili). `deploy/` altındaki her `.service`in (bilinen ölüler hariç) bu
glob'larca kapsandığını v451 Çivi 2a ölçer — yeni bir docker birimi ya kapsama girer ve bu çivi onu ELLE LİSTE
OLMADAN görür (C1), ya da v451 kırmızı olur. KÖRLÜK KORUMASI (A0b): yönerge metninde `docker … run` geçip
ayrıştırıcının docker-run olarak tanımadığı komut (ör. `sh -c "docker run …"`) BULGUDUR, sessizce atlanmaz.

RUNBOOK (D). `deploy/oracle-a1/RUNBOOK.md` "Docker konteyner bellek tavanı" bölümündeki `docker inspect` beklenen
satırı konteyner ADIYLA birimin `--memory` baytına eşittir: tavan birimde değişip doğrulama cetvelinde kalırsa canlı
doğrulama DOĞRU birimi "ayrık" okur (v584 A5 emsali, Grafana tur 3).

CPU EŞİ (E, TSK-247(b), 2026-09-28). Aynı sınıfın CPU kopyası. Rol-1 A1 ölçümü (salt-okur): `systemctl show -p
CPUQuotaPerSecUSec hindsight-cp` = 1s — yalnız docker İSTEMCİ süreci; `docker inspect` NanoCpus=0 / CpuQuota=0 →
konteyner CPU'su SINIRSIZ. KURAL (E): bir görünümde `CPUQuota=` BEYAN EDEN her docker-run komutunda `--cpus` TAM BİR kez
bulunur ve `CPUQuota/100`e eşittir (nano-CPU olarak: `CPUQuota=100%` ↔ `--cpus=1` ↔ `HostConfig.NanoCpus`
1000000000). `CPUQuota` beyan ETMEYEN (ya da boş atamayla sıfırlayan) birimde `--cpus` ZORUNLU DEĞİL — bugünkü tasarım:
yalnız hindsight-cp CPU kotası taşır (telemetri ve apisix birimleri taşımaz). systemd'nin uyarıyla YOK SAYDIĞI kota
(`0%`, yüzdesiz yazım) bulgudur (niyet yürürlüğe girmez); `‰`/`‱` yazımı da bulgu verir (geçerli ama modellenmedi —
güvenli yön). `--cpu-quota`/`--cpu-period`/`--cpu-shares` `--cpus` SAYILMAZ. `--cpus` v584 `_DEGERLI` kümesindedir
(ayrı jetonlu `--cpus 1` imajı kaydırmasın). RUNBOOK cetvelindeki `NanoCpus` beklenen satırı birimin `--cpus`una
eşittir (D3).

MODELLENMEYEN (bilinçli): `docker compose` (kurulan birimlerde yok; kök `deploy/meridian.service` compose çağının
kalıntısıdır ve kapsam dışıdır); `--memory-swap` (brief: swap bayrağı eklenmez, emsalle tutarlı); `--cpus` ile
`--cpu-quota`/`--cpu-period`in BİRLİKTE yazımı (docker kaynağı okumasına göre konteyneri açmaz — ÖLÇÜLMEDİ; açmazsa
sessiz değil, birim düşer ve RUNBOOK `is-active` satırı görür); `--cpus` taşıyıp `CPUQuota` beyan etmeyen birim
(konteyner sınırlı, istemci değil — brief: zorunlu değil, yasak da değil).

Numara v587: ana checkout + worktree'lerde boş (ölçüldü 2026-09-28). Bu dosya hiçbir `state/` yolu okumaz/yazmaz;
sentetik birimler `tmp_path` altında kurulur.
"""
from __future__ import annotations

import dataclasses
import glob
import posixpath
import re
import shlex
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

# Tek-kaynak: birim sözdizimi (yorum + `\\` devamı), drop-in sırası ve A0 birim türetimi v553'te yaşar.
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _depo_birimleri, _dropinler, _yonergeler
# Tek-kaynak: süreç doğuran yönerge kümesi v554'te yaşar.
from tests.test_birim_argv_sir_v554 import KOMUT_YONERGELERI
# Tek-kaynak: `docker run` seçenek ayrıştırması v584'te yaşar.
from tests.test_telemetri_altyapi_v584 import _docker_run

KOK = Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy"
ANSIBLE = DEPLOY / "ansible"
DEFAULTS = ANSIBLE / "roles" / "meridian_a1" / "defaults" / "main.yml"
TELEMETRI = DEPLOY / "telemetri"
RUNBOOK_A1 = DEPLOY / "oracle-a1" / "RUNBOOK.md"
RUNBOOK_BASLIK = "## Docker konteyner bellek tavanı"

#: Brief'in ölçtüğü üç konteyner (Rol-1 A1, 2026-09-28) — kapsam LİSTESİ değil, türetilmiş kapsamın KÖR olmadığının
#: çapası (A0b) ve RUNBOOK doğrulama cetvelinin asgarisi (D1).
BRIEF_KONTEYNERLERI = frozenset({"apisix-kapi", "apisix-etcd", "hindsight-cp"})
#: TSK-247(b) brief'inin ölçtüğü CPU kotalı docker birimi (Rol-1 depo + A1, 2026-09-28) — E0 körlük çapası ve RUNBOOK
#: NanoCpus cetvelinin asgarisi (D3). Kapsam listesi DEĞİL: E1 türetilmiş kümenin tamamını denetler.
CPU_BRIEF_KONTEYNERLERI = frozenset({"hindsight-cp"})

#: systemd Exec önekleri (systemd.service(5) "Command lines"): `@` `-` `:` `+` `!` `!!` `|`.
_EXEC_ONEKLERI = "@-:+!|"
#: Ham metin körlük koruması: yönerge değerinde `docker [container] run` — tırnak içi (`sh -c "…"`) dahil.
_DOCKER_RUN_METNI = re.compile(r"(?:^|[\s/\"'])docker\s+(?:container\s+)?run(?=[\s\"']|$)")
#: systemd boyut sözdizimi (parse_size, 1024 tabanı): son ek YALNIZ büyük harf; `infinity`/yüzde sonlu bayt değildir.
_SYSTEMD_BOYUT = re.compile(r"(\d+(?:\.\d+)?)([KMGTPE]?)")
#: docker boyut sözdizimi (go-units `RAMInBytes`, 1024 tabanı): `512m` `512M` `512MB` `512MiB` `512 m` `536870912`.
_DOCKER_BOYUT = re.compile(r"(\d+(?:\.\d+)?) ?([kmgtp]?)i?b?", re.IGNORECASE)
_CARPAN = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4, "P": 1024 ** 5, "E": 1024 ** 6}
#: systemd `CPUQuota=` (config_parse_cpu_quota → parse_permyriad_unbounded): yüzde, en çok iki ondalık. Boş atama kotayı
#: kaldırır; `0%` ve sözdizimi dışı değer uyarıyla YOK SAYILIR. `‰`/`‱` geçerlidir ama burada modellenmez (bulgu verir).
#: Kaynak: systemd kaynak kodu OKUMASI — A1'de ÖLÇÜLMEDİ; yanılgı yönü yanlış alarmdır (fazladan bulgu), sessiz yeşil değil.
_SYSTEMD_CPU = re.compile(r"(\d+(?:\.\d{1,2})?)%")
#: docker `--cpus` (opts.NanoCPUs → big.Rat × 10^9, tam sayı olmalı): ondalık yazım. `0` = TAVANSIZ (NanoCpus 0).
#: Kesir (`3/2`) ve üslü yazım docker'da geçerlidir ama burada modellenmez (bulgu verir — güvenli yön). Kaynak: docker
#: CLI kaynak kodu OKUMASI (A1'de ölçülen tek nokta: `--cpus` yokken NanoCpus=0).
_DOCKER_CPU = re.compile(r"\d+(?:\.\d+)?|\.\d+")
_NANO = 10 ** 9


# =================================================================================================
# Ayrıştırıcılar
# =================================================================================================

def _systemd_bayt(deger: str) -> int | None:
    m = _SYSTEMD_BOYUT.fullmatch(deger.strip())
    return int(float(m[1]) * _CARPAN[m[2]]) if m else None


def _docker_bayt(deger: str) -> int | None:
    m = _DOCKER_BOYUT.fullmatch(deger.strip())
    return int(float(m[1]) * _CARPAN[m[2].upper()]) if m else None


def _nano_tam(oran: Fraction) -> int | None:
    """Çekirdek oranı → nano-CPU; sıfır/negatif (tavansız) ya da 10^-9'dan ince değer None."""
    nano = oran * _NANO
    return int(nano) if nano > 0 and nano.denominator == 1 else None


def _cpuquota_nano(deger: str) -> int | None:
    """`CPUQuota=100%` → 1000000000 nano-CPU (1 çekirdek; docker `NanoCpus` birimi)."""
    m = _SYSTEMD_CPU.fullmatch(deger.strip())
    return _nano_tam(Fraction(m[1]) / 100) if m else None


def _docker_nano_cpu(deger: str) -> int | None:
    """`--cpus=1` → 1000000000 nano-CPU (`docker inspect` `HostConfig.NanoCpus`)."""
    d = deger.strip()
    return _nano_tam(Fraction(d)) if _DOCKER_CPU.fullmatch(d) else None


def _docker_run_argumanlari(deger: str) -> list[str] | None:
    """Komut `docker run`/`docker container run` ise `run`dan SONRAKİ jetonlar; değilse None."""
    j = shlex.split(deger)
    if not j or posixpath.basename(j[0].lstrip(_EXEC_ONEKLERI)) != "docker":
        return None
    if j[1:2] == ["run"]:
        return j[2:]
    if j[1:3] == ["container", "run"]:
        return j[3:]
    return None


def _bellek_degerleri(secenekler: list[tuple[str, str | None]]) -> list[str]:
    """`--memory=X` · `--memory X` · `-m X` → X; v584 ayrıştırıcısı `-m=X`/`-mX`i değersiz bir ad olarak döndürür."""
    out: list[str] = []
    for ad, deger in secenekler:
        if ad in ("--memory", "-m"):
            out.append(str(deger))
        elif ad.startswith("-m") and not ad.startswith("--"):
            out.append(ad[2:].removeprefix("="))
    return out


def _imaj_gibi(imaj: str) -> bool:
    """İmaj başvurusu: küçük harf/rakamla başlar ve SON yol parçası bir etiket ya da özet taşır."""
    son = imaj.rsplit("/", 1)[-1]
    return bool(re.match(r"[a-z0-9]", imaj)) and bool(re.search(r"(?::[\w.-]+|@sha256:[0-9a-f]{64})$", son))


@dataclasses.dataclass
class _Gorunum:
    """Bir birimin bir görünümdeki [Service] komutları (sıfırlamalar uygulanmış), MemoryMax'ı ve CPUQuota'sı."""
    birim: str
    kip: str                                   # "birim" | "birlesik"
    komutlar: list[tuple[str, str, Path]]      # (yönerge, değer, kaynak dosya)
    memory_max: tuple[str, Path] | None        # None: hiç yazılmamış ya da boş atamayla sıfırlanmış
    cpu_quota: tuple[str, Path] | None = None  # aynı skaler kural (son yazan kazanır; boş atama kotayı kaldırır)


def _gorunum(birim: Path, kip: str, kaynaklar: list[Path]) -> _Gorunum:
    komutlar: dict[str, list[tuple[str, Path]]] = {}
    memory_max: tuple[str, Path] | None = None
    cpu_quota: tuple[str, Path] | None = None
    for kaynak in kaynaklar:
        for bolum, anahtar, deger in _yonergeler(kaynak.read_text(encoding="utf-8")):
            if bolum != "Service":
                continue
            if anahtar in KOMUT_YONERGELERI:
                if deger:
                    komutlar.setdefault(anahtar, []).append((deger, kaynak))
                else:
                    komutlar[anahtar] = []
            elif anahtar == "MemoryMax":
                memory_max = (deger, kaynak) if deger else None
            elif anahtar == "CPUQuota":
                cpu_quota = (deger, kaynak) if deger else None
    duz = [(a, d, k) for a, liste in komutlar.items() for d, k in liste]
    return _Gorunum(birim.name, kip, duz, memory_max, cpu_quota)


def _gorunumler(birim: Path) -> list[_Gorunum]:
    out = [_gorunum(birim, "birim", [birim])]
    dropinler = _dropinler(birim)
    if dropinler:
        out.append(_gorunum(birim, "birlesik", [birim, *dropinler]))
    return out


def _goreli(p: Path) -> str:
    return str(p.relative_to(KOK)) if p.is_relative_to(KOK) else p.name


def _docker_komutlari(birim: Path):
    """(görünüm, yönerge, değer, kaynak, ayrışmış run) — yalnız docker-run komutları."""
    for g in _gorunumler(birim):
        for anahtar, deger, kaynak in g.komutlar:
            argv = _docker_run_argumanlari(deger)
            if argv is not None:
                yield g, anahtar, deger, kaynak, _docker_run(shlex.join(["/usr/bin/docker", "run", *argv]))


# =================================================================================================
# Denetçi — gerçek depo ve sentetik birimler AYNI fonksiyondan geçer
# =================================================================================================

def _bulgular(birimler: list[Path]) -> list[dict]:
    b: list[dict] = []
    for birim in birimler:
        for g in _gorunumler(birim):
            for anahtar, deger, kaynak in g.komutlar:
                ortak = {"birim": g.birim, "gorunum": g.kip, "yonerge": anahtar, "kaynak": _goreli(kaynak)}
                argv = _docker_run_argumanlari(deger)
                if argv is None:
                    if _DOCKER_RUN_METNI.search(deger):
                        b.append({"tur": "taninmayan_docker_run", **ortak, "komut": deger[:120]})
                    continue
                run = _docker_run(shlex.join(["/usr/bin/docker", "run", *argv]))
                if not _imaj_gibi(run.imaj):
                    b.append({"tur": "imaj_jetonu_supheli", **ortak, "imaj": run.imaj})
                bellek = _bellek_degerleri(run.secenekler)
                if not bellek:
                    b.append({"tur": "memory_yok", **ortak})
                elif len(bellek) > 1:
                    b.append({"tur": "memory_coklu", **ortak, "degerler": bellek})
                mm_bayt = None
                if g.memory_max is None:
                    b.append({"tur": "memorymax_yok", **ortak})
                else:
                    mm_bayt = _systemd_bayt(g.memory_max[0])
                    if mm_bayt is None:
                        b.append({"tur": "memorymax_sonlu_bayt_degil", **ortak, "MemoryMax": g.memory_max[0]})
                if len(bellek) == 1:
                    d_bayt = _docker_bayt(bellek[0])
                    if d_bayt is None:
                        b.append({"tur": "memory_ayrisamadi", **ortak, "memory": bellek[0]})
                    elif mm_bayt is not None and d_bayt != mm_bayt:
                        b.append({"tur": "esit_degil", **ortak, "memory": bellek[0],
                                  "MemoryMax": g.memory_max[0] if g.memory_max else None})
    return b


def _bicimle(bulgular: list[dict]) -> str:
    return "\n".join(f"  · {x}" for x in bulgular)


def _cpu_bulgulari(birimler: list[Path]) -> list[dict]:
    """E kuralı. Tanınmayan docker-run ve imaj kayması `_bulgular`da (A1) öter — burada tekrar sayılmaz; kayan bir
    `--cpus` kapsayıcı argümanına düşer ve `cpus_yok` olarak da öter (güvenli yön)."""
    b: list[dict] = []
    for g, anahtar, _deger, kaynak, run in (x for p in birimler for x in _docker_komutlari(p)):
        if g.cpu_quota is None:
            continue  # CPUQuota beyan etmeyen görünüm: `--cpus` zorunlu değil (bugünkü tasarım, brief)
        ortak = {"birim": g.birim, "gorunum": g.kip, "yonerge": anahtar, "kaynak": _goreli(kaynak),
                 "CPUQuota": g.cpu_quota[0]}
        kota = _cpuquota_nano(g.cpu_quota[0])
        if kota is None:
            b.append({"tur": "cpuquota_gecersiz", **ortak})
        cpus = [str(d) for a, d in run.secenekler if a == "--cpus"]
        if not cpus:
            b.append({"tur": "cpus_yok", **ortak})
        elif len(cpus) > 1:
            b.append({"tur": "cpus_coklu", **ortak, "degerler": cpus})
        else:
            nano = _docker_nano_cpu(cpus[0])
            if nano is None:
                b.append({"tur": "cpus_gecersiz", **ortak, "cpus": cpus[0]})
            elif kota is not None and nano != kota:
                b.append({"tur": "cpus_esit_degil", **ortak, "cpus": cpus[0]})
    return b


# =================================================================================================
# Depo girdileri (tek kaynak: A0 rolü)
# =================================================================================================

def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _birimler(desenler: list[str], ansible_kok: Path) -> list[Path]:
    """`birim_kaynaklari` glob'ları → `.service` dosyaları; `{{ playbook_dir }}` = verilen ansible kökü."""
    bulunan: set[Path] = set()
    for desen in desenler:
        if desen.endswith(".service"):
            bulunan |= {Path(p).resolve() for p in glob.glob(desen.replace("{{ playbook_dir }}", str(ansible_kok)))}
    return sorted(bulunan)


def _depo() -> list[Path]:
    return _birimler(_defaults()["birim_kaynaklari"], ANSIBLE)


def _docker_birimleri(birimler: list[Path]) -> list[Path]:
    return [p for p in birimler if any(True for _ in _docker_komutlari(p))]


def _konteyner_adlari(birimler: list[Path]) -> set[str]:
    """docker-run komutlarının `--name` değerleri — tavandan BAĞIMSIZ (körlük çapası tavan yokken de görmeli)."""
    return {str(d) for p in birimler for *_x, run in _docker_komutlari(p) for a, d in run.secenekler if a == "--name"}


def _konteyner_bellekleri(birimler: list[Path]) -> dict[str, set[int]]:
    """Konteyner adı (`--name`) → birimlerin HER görünümündeki `--memory` baytları."""
    out: dict[str, set[int]] = {}
    for p in birimler:
        for _g, _a, _d, _k, run in _docker_komutlari(p):
            adlar = [d for a, d in run.secenekler if a == "--name"]
            bellek = _bellek_degerleri(run.secenekler)
            if len(adlar) == 1 and len(bellek) == 1 and _docker_bayt(bellek[0]) is not None:
                out.setdefault(str(adlar[0]), set()).add(_docker_bayt(bellek[0]))
    return out


def _konteyner_cpulari(birimler: list[Path]) -> dict[str, set[int | None]]:
    """Konteyner adı → birimlerin HER görünümündeki `--cpus` nano-CPU'su (`--cpus`suz görünüm: None)."""
    out: dict[str, set[int | None]] = {}
    for p in birimler:
        for _g, _a, _d, _k, run in _docker_komutlari(p):
            adlar = [d for a, d in run.secenekler if a == "--name"]
            cpus = [str(d) for a, d in run.secenekler if a == "--cpus"]
            if len(adlar) == 1:
                out.setdefault(str(adlar[0]), set()).add(_docker_nano_cpu(cpus[0]) if len(cpus) == 1 else None)
    return out


def _cpu_kotali_konteynerler(birimler: list[Path]) -> set[str]:
    """`CPUQuota=` beyan eden görünümlerdeki docker-run komutlarının `--name`leri — `--cpus`tan BAĞIMSIZ (E0 körlük
    çapası tavan yokken de görmeli)."""
    return {str(d) for p in birimler for g, *_x, run in _docker_komutlari(p) if g.cpu_quota is not None
            for a, d in run.secenekler if a == "--name"}


# =================================================================================================
# A — gerçek depo
# =================================================================================================

def test_A0_kapsam_A0_rolunden_TURER_ve_v553_turetimiyle_ESIT():
    birimler = _depo()
    assert birimler, "birim_kaynaklari hiçbir .service çözmedi — yol yanlış, çivi kör"
    assert birimler == _depo_birimleri(), (
        "v587 türetimi v553 `_depo_birimleri` ile ayrıştı — iki türetim, tek gerçek (tek-kaynak yasası)")


def test_A0b_KORLUK_KORUMASI_ayristirici_ham_metinle_AYNI_docker_kumesini_gorur():
    """Ayrıştırıcının docker-run saydığı birim kümesi = yönerge metninde `docker … run` geçen birim kümesi.
    Ayrışma ya tanınmayan bir biçimdir (A1'de `taninmayan_docker_run` olarak da öter) ya da ayrıştırıcı körlüğü."""
    birimler = _depo()
    ayristirici = {p.name for p in _docker_birimleri(birimler)}
    ham = {p.name for p in birimler for g in _gorunumler(p) for _a, d, _k in g.komutlar if _DOCKER_RUN_METNI.search(d)}
    assert ayristirici == ham, f"ayrıştırıcı ↔ ham metin ayrıştı: yalnız ham {sorted(ham - ayristirici)}"
    konteynerler = _konteyner_adlari(birimler)
    assert BRIEF_KONTEYNERLERI <= konteynerler, (
        f"brief'in ölçtüğü konteynerler kapsamda görünmüyor (çivi kör): {sorted(BRIEF_KONTEYNERLERI - konteynerler)}")


def test_A0c_POZITIF_KONTROL_birlesik_gorunum_drop_in_ExecStartini_OKUR():
    """apisix drop-in'i ExecStart'ı sıfırlayıp yeniden yazar: birleşik görünümdeki TEK docker komutu drop-in'den gelir
    ve yan dosyayı taşır. Birleştirme kırıksa (sıfırlama uygulanmıyorsa) iki komut görünür ya da kaynak yanlış olur."""
    apisix = next(p for p in _depo() if p.name == "apisix.service")
    birlesik = [(g, k, d) for g, _a, d, k, _r in _docker_komutlari(apisix) if g.kip == "birlesik"]
    assert len(birlesik) == 1, f"birleşik görünümde docker komutu {len(birlesik)} (sıfırlama modellenmemiş)"
    _g, kaynak, deger = birlesik[0]
    assert kaynak.parent.name == "apisix.service.d" and ".env-apisix.vault" in deger, (
        f"birleşik ExecStart drop-in'den gelmiyor: {_goreli(kaynak)}")


def test_A1_HER_docker_biriminde_konteyner_tavani_MemoryMax_ile_ESIT():
    bulgular = _bulgular(_depo())
    assert not bulgular, (
        "docker birimi konteyner bellek tavanı taşımıyor ya da MemoryMax'tan ayrışıyor:\n"
        f"{_bicimle(bulgular)}\n"
        "ÇARE: `docker run`a `--memory=<MemoryMax ile aynı>` (emsal deploy/telemetri/meridian-prometheus.service); "
        "`MemoryMax=` YALNIZ docker istemcisini sınırlar. ExecStart'ı yeniden yazan drop-in varsa bayrak orada da.")


def test_A2_POZITIF_KONTROL_telemetri_birimleri_kapsamda_ve_GECER():
    """Telemetri birimleri (v584 emsali) iki katmanı zaten taşır: bu çivi onları KAPSAMALI ve GEÇİRMELİ."""
    birimler = _depo()
    telemetri = [p for p in _docker_birimleri(birimler) if p.parent == TELEMETRI.resolve()]
    beklenen = {p.resolve() for p in TELEMETRI.glob("*.service")}
    assert beklenen and set(telemetri) == beklenen, (
        f"telemetri birimleri docker kapsamında değil: {sorted(p.name for p in beklenen - set(telemetri))}")
    assert _bulgular(telemetri) == [], _bicimle(_bulgular(telemetri))


# =================================================================================================
# B — pozitif kontrol: gerçek birim metni bellekte bozulur, AYNI denetçi öter / ötmez
# =================================================================================================

def _sahte(kok: Path, ad: str, govde: str, dropin: str | None = None) -> Path:
    kok.mkdir(parents=True, exist_ok=True)
    birim = kok / f"{ad}.service"
    birim.write_text(govde, encoding="utf-8")
    if dropin is not None:
        d = kok / f"{ad}.service.d"
        d.mkdir(exist_ok=True)
        (d / "50-sahte.conf").write_text(dropin, encoding="utf-8")
    return birim


def _bozuk(metin: str, eski: str, yeni: str) -> str:
    assert metin.count(eski) == 1, f"mutasyon çapası dosyada TEK değil (çivi bayatlamış): {eski!r}"
    return metin.replace(eski, yeni, 1)


ETCD = DEPLOY / "apisix" / "apisix-etcd.service"

OTEN_MUTASYONLAR = [
    ("memory_silindi", "  --memory=256m \\\n", "", "memory_yok"),
    ("deger_farkli", "--memory=256m", "--memory=128m", "esit_degil"),
    ("swap_bayragi_memory_sayilmaz", "--memory=256m", "--memory-swap=256m", "memory_yok"),
    ("rezervasyon_memory_sayilmaz", "--memory=256m", "--memory-reservation=256m", "memory_yok"),
    ("ikinci_memory", "--memory=256m", "--memory=256m -m 256m", "memory_coklu"),
    ("memory_ayrismaz", "--memory=256m", "--memory=yarim", "memory_ayrisamadi"),
    ("memorymax_silindi", "MemoryMax=256M\n", "", "memorymax_yok"),
    ("memorymax_bos_sifirlama", "MemoryMax=256M", "MemoryMax=", "memorymax_yok"),
    ("memorymax_kucuk_harf", "MemoryMax=256M", "MemoryMax=256m", "memorymax_sonlu_bayt_degil"),
    ("memorymax_sonsuz", "MemoryMax=256M", "MemoryMax=infinity", "memorymax_sonlu_bayt_degil"),
    ("memorymax_yuzde", "MemoryMax=256M", "MemoryMax=5%", "memorymax_sonlu_bayt_degil"),
    ("memorymax_farkli", "MemoryMax=256M", "MemoryMax=1G", "esit_degil"),
]


@pytest.mark.parametrize("kimlik, eski, yeni, beklenen", OTEN_MUTASYONLAR, ids=[m[0] for m in OTEN_MUTASYONLAR])
def test_B1_POZITIF_KONTROL_bozuk_birimde_denetci_OTER(tmp_path, kimlik, eski, yeni, beklenen):
    birim = _sahte(tmp_path, "apisix-etcd", _bozuk(ETCD.read_text(encoding="utf-8"), eski, yeni))
    turler = [x["tur"] for x in _bulgular([birim])]
    assert beklenen in turler, f"{kimlik}: denetçi ÖTMEDİ: {turler}"


ESDEGER_YAZIMLAR = [
    ("ayri_jeton", "--memory=256m", "--memory 256m"),
    ("kisa_ayri", "--memory=256m", "-m 256m"),
    ("kisa_bitisik", "--memory=256m", "-m256m"),
    ("kisa_esittir", "--memory=256m", "-m=256m"),
    ("buyuk_harf", "--memory=256m", "--memory=256M"),
    ("mib", "--memory=256m", "--memory=256MiB"),
    ("bayt", "--memory=256m", "--memory=268435456"),
    ("memorymax_bayt", "MemoryMax=256M", "MemoryMax=268435456"),
]


@pytest.mark.parametrize("kimlik, eski, yeni", ESDEGER_YAZIMLAR, ids=[m[0] for m in ESDEGER_YAZIMLAR])
def test_B2_NEGATIF_KONTROL_esdeger_yazimda_denetci_SUSAR(tmp_path, kimlik, eski, yeni):
    birim = _sahte(tmp_path, "apisix-etcd", _bozuk(ETCD.read_text(encoding="utf-8"), eski, yeni))
    assert _bulgular([birim]) == [], f"{kimlik}: eşdeğer yazımda yanlış alarm: {_bulgular([birim])}"


APISIX = DEPLOY / "apisix" / "apisix.service"
APISIX_DROPIN = DEPLOY / "apisix" / "apisix.service.d" / "50-vault-yan-dosya.conf"

DROPIN_MUTASYONLARI = [
    ("dropin_ExecStart_memorysiz", "  --memory=512m \\\n", "", "memory_yok"),
    ("dropin_MemoryMax_sifirlar", "[Service]\n", "[Service]\nMemoryMax=\n", "memorymax_yok"),
    ("dropin_MemoryMax_degistirir", "[Service]\n", "[Service]\nMemoryMax=1G\n", "esit_degil"),
]


@pytest.mark.parametrize("kimlik, eski, yeni, beklenen", DROPIN_MUTASYONLARI, ids=[m[0] for m in DROPIN_MUTASYONLARI])
def test_B3_POZITIF_KONTROL_drop_in_BIRLESIK_gorunumu_bozar_birim_gorunumu_TEMIZ(tmp_path, kimlik, eski, yeni, beklenen):
    """Drop-in yalnız BİRLEŞİK görünümü bozar: temel birim tek başına temiz kalır. Yalnız temel birimi okuyan bir
    çivi bu hâli (A1'de koşan komut tavansız) GÖREMEZDİ."""
    birim = _sahte(tmp_path, "apisix", APISIX.read_text(encoding="utf-8"),
                   dropin=_bozuk(APISIX_DROPIN.read_text(encoding="utf-8"), eski, yeni))
    bulgular = _bulgular([birim])
    assert [x["tur"] for x in bulgular if x["gorunum"] == "birlesik"].count(beklenen) >= 1, f"{kimlik}: {bulgular}"
    assert [x for x in bulgular if x["gorunum"] == "birim"] == [], f"{kimlik}: temel birim bozuk görünüyor: {bulgular}"


def test_B4_POZITIF_KONTROL_sarmalanmis_docker_run_TANINMAYAN_diye_OTER(tmp_path):
    birim = _sahte(tmp_path, "sarmal", "[Service]\nExecStart=/bin/sh -c \"exec /usr/bin/docker run --rm img:1\"\n"
                                       "MemoryMax=64M\n")
    assert [x["tur"] for x in _bulgular([birim])] == ["taninmayan_docker_run"]


def test_B5_POZITIF_KONTROL_taninmayan_degerli_bayrak_imaji_kaydirir_ve_OTER(tmp_path):
    """`--cpu-shares` v584 `_DEGERLI` kümesinde yok → değersiz sayılır → `512` imaj olur, `--memory` kapsayıcı
    argümanına düşer. Güvenli yön: hem kayma (`imaj_jetonu_supheli`) hem tavan yokluğu öter; sessiz yeşil yok.
    (TSK-247(b)'ye dek örnek `--cpus 2` idi; `--cpus` artık `_DEGERLI`de — E bölümü onu ayrı jetonla da okur.)"""
    birim = _sahte(tmp_path, "kayik", "[Service]\nExecStart=/usr/bin/docker run --rm --cpu-shares 512 --memory=64m img:1\n"
                                      "MemoryMax=64M\n")
    turler = {x["tur"] for x in _bulgular([birim])}
    assert {"imaj_jetonu_supheli", "memory_yok"} <= turler, turler


def test_B6_NEGATIF_KONTROL_docker_run_KOSMAYAN_birim_kapsam_disi(tmp_path):
    """`docker rm`/`docker stop` ve docker'sız süreçler bu çivinin konusu değil (MemoryMax orada süreci sınırlar)."""
    birim = _sahte(tmp_path, "dockersiz", "[Service]\nExecStartPre=-/usr/bin/docker rm -f x\n"
                                          "ExecStart=/usr/bin/python3 -m http.server\nExecStop=/usr/bin/docker stop x\n")
    assert _bulgular([birim]) == []


# =================================================================================================
# C — yeni docker birimi DOĞDUĞU GÜN kapsama girer (elle liste yok)
# =================================================================================================

def test_C1_yeni_sahte_docker_birimi_GERCEK_globlarla_kapsama_girer_ve_OTER(tmp_path):
    """Gerçek `birim_kaynaklari` glob'ları sahte bir `playbook_dir`e köklenir; glob'un kapsadığı bir dizine konan YENİ
    bir docker birimi hiçbir liste düzenlenmeden türetilen kümeye girer ve tavansız olduğu için öter."""
    ansible = tmp_path / "ansible"
    ansible.mkdir()
    yeni = _sahte(tmp_path / "apisix", "sahte-kutu",
                  "[Service]\nExecStart=/usr/bin/docker run --rm --name sahte-kutu img:1.0\nMemoryMax=128M\n")
    birimler = _birimler(_defaults()["birim_kaynaklari"], ansible)
    assert yeni.resolve() in birimler, f"yeni birim türetilmiş kapsamda değil: {birimler}"
    assert [(x["birim"], x["tur"]) for x in _bulgular(birimler)] == [("sahte-kutu.service", "memory_yok")]


# =================================================================================================
# D — RUNBOOK doğrulama cetveli ↔ birim
# =================================================================================================

def _runbook_bolumu(metin: str) -> str:
    i = metin.find(RUNBOOK_BASLIK)
    assert i >= 0, f"RUNBOOK'ta '{RUNBOOK_BASLIK}' bölümü yok"
    j = metin.find("\n## ", i + 1)
    return metin[i:] if j < 0 else metin[i:j]


def _runbook_bulgulari(metin: str, bellekler: dict[str, set[int]]) -> list[str]:
    bolum = _runbook_bolumu(metin)
    m = re.search(r'docker inspect -f "\{\{\.Name\}\} \{\{\.HostConfig\.Memory\}\}" ([\w -]+)\'\n# beklenen: ([^\n]+)',
                  bolum)
    if not m:
        return ["RUNBOOK: `docker inspect … {{.HostConfig.Memory}}` + `# beklenen:` satırı bulunamadı"]
    adlar = m.group(1).split()
    beklenen = {ad: int(b) for ad, b in re.findall(r"/([\w-]+) (\d+)", m.group(2))}
    b: list[str] = []
    if sorted(adlar) != sorted(beklenen):
        b.append(f"RUNBOOK inspect komutundaki adlar ↔ beklenen satırı ayrıştı: {adlar} / {sorted(beklenen)}")
    if not BRIEF_KONTEYNERLERI <= set(beklenen):
        b.append(f"RUNBOOK cetveli brief konteynerlerini taşımıyor: {sorted(BRIEF_KONTEYNERLERI - set(beklenen))}")
    for ad, bayt in beklenen.items():
        birimde = bellekler.get(ad)
        if not birimde:
            b.append(f"RUNBOOK: {ad} hiçbir docker biriminin `--name`i değil")
        elif birimde != {bayt}:
            b.append(f"RUNBOOK: {ad} beklenen {bayt} != birim `--memory` {sorted(birimde)}")
    return b


def test_D1_RUNBOOK_inspect_beklenenleri_birim_tavanlarina_ESIT():
    bulgular = _runbook_bulgulari(RUNBOOK_A1.read_text(encoding="utf-8"), _konteyner_bellekleri(_depo()))
    assert bulgular == [], "RUNBOOK doğrulama cetveli birimden ayrıştı:\n" + "\n".join(bulgular)


RUNBOOK_MUTASYONLARI = [
    ("etcd_eski_deger", "/apisix-etcd 268435456", "/apisix-etcd 0", "beklenen 0"),
    ("kapi_eksik", "/apisix-kapi 536870912 · ", "", "ayrıştı"),
]


@pytest.mark.parametrize("kimlik, eski, yeni, beklenen", RUNBOOK_MUTASYONLARI, ids=[m[0] for m in RUNBOOK_MUTASYONLARI])
def test_D2_POZITIF_KONTROL_runbook_denetcisi_OTER(kimlik, eski, yeni, beklenen):
    bozuk = _bozuk(RUNBOOK_A1.read_text(encoding="utf-8"), eski, yeni)
    bulgular = _runbook_bulgulari(bozuk, _konteyner_bellekleri(_depo()))
    assert any(beklenen in x for x in bulgular), f"{kimlik}: denetçi ÖTMEDİ: {bulgular}"


def _runbook_cpu_bulgulari(metin: str, cpular: dict[str, set[int | None]]) -> list[str]:
    """RUNBOOK TSK-247 bölümündeki `{{.HostConfig.NanoCpus}}` beklenen satırı ↔ birimin `--cpus`u (nano-CPU)."""
    bolum = _runbook_bolumu(metin)
    m = re.search(
        r'docker inspect -f "\{\{\.Name\}\} \{\{\.HostConfig\.NanoCpus\}\}" ([\w -]+)\'\n# beklenen: ([^\n]+)', bolum)
    if not m:
        return ["RUNBOOK: `docker inspect … {{.HostConfig.NanoCpus}}` + `# beklenen:` satırı bulunamadı"]
    adlar = m.group(1).split()
    beklenen = {ad: int(n) for ad, n in re.findall(r"/([\w-]+) (\d+)", m.group(2))}
    b: list[str] = []
    if sorted(adlar) != sorted(beklenen):
        b.append(f"RUNBOOK NanoCpus inspect adları ↔ beklenen satırı ayrıştı: {adlar} / {sorted(beklenen)}")
    if not CPU_BRIEF_KONTEYNERLERI <= set(beklenen):
        b.append(f"RUNBOOK NanoCpus cetveli brief konteynerini taşımıyor: {sorted(CPU_BRIEF_KONTEYNERLERI - set(beklenen))}")
    for ad, nano in beklenen.items():
        birimde = cpular.get(ad)
        if not birimde:
            b.append(f"RUNBOOK NanoCpus: {ad} hiçbir docker biriminin `--name`i değil")
        elif birimde != {nano}:
            b.append(f"RUNBOOK NanoCpus: {ad} beklenen {nano} != birim `--cpus` nano {sorted(birimde, key=str)}")
    return b


def test_D3_RUNBOOK_NanoCpus_beklenenleri_birim_cpus_ESIT():
    bulgular = _runbook_cpu_bulgulari(RUNBOOK_A1.read_text(encoding="utf-8"), _konteyner_cpulari(_depo()))
    assert bulgular == [], "RUNBOOK CPU doğrulama cetveli birimden ayrıştı:\n" + "\n".join(bulgular)


RUNBOOK_CPU_MUTASYONLARI = [
    ("cp_tavansiz_deger", "/hindsight-cp 1000000000", "/hindsight-cp 0", "beklenen 0"),
    ("cp_iki_cekirdek", "/hindsight-cp 1000000000", "/hindsight-cp 2000000000", "beklenen 2000000000"),
    ("cp_cetvelden_cikti", "/hindsight-cp 1000000000", "", "ayrıştı"),
]


@pytest.mark.parametrize("kimlik, eski, yeni, beklenen", RUNBOOK_CPU_MUTASYONLARI,
                         ids=[m[0] for m in RUNBOOK_CPU_MUTASYONLARI])
def test_D4_POZITIF_KONTROL_runbook_cpu_denetcisi_OTER(kimlik, eski, yeni, beklenen):
    bozuk = _bozuk(RUNBOOK_A1.read_text(encoding="utf-8"), eski, yeni)
    bulgular = _runbook_cpu_bulgulari(bozuk, _konteyner_cpulari(_depo()))
    assert any(beklenen in x for x in bulgular), f"{kimlik}: denetçi ÖTMEDİ: {bulgular}"


# =================================================================================================
# E — CPU eşi (TSK-247(b)): CPUQuota beyan eden docker biriminde `--cpus` = CPUQuota/100
# =================================================================================================

def test_E0_KORLUK_CAPASI_cpu_kotali_docker_birimleri_GORUNUR():
    konteynerler = _cpu_kotali_konteynerler(_depo())
    assert CPU_BRIEF_KONTEYNERLERI <= konteynerler, (
        f"brief'in ölçtüğü CPU kotalı konteyner kapsamda görünmüyor (E kör): {sorted(CPU_BRIEF_KONTEYNERLERI - konteynerler)}")


def test_E1_CPUQuota_beyan_eden_HER_docker_biriminde_konteyner_cpus_ESIT():
    bulgular = _cpu_bulgulari(_depo())
    assert not bulgular, (
        "CPUQuota beyan eden docker birimi konteyner CPU tavanı taşımıyor ya da CPUQuota/100'den ayrışıyor:\n"
        f"{_bicimle(bulgular)}\n"
        "ÇARE: `docker run`a `--cpus=<CPUQuota/100>` (CPUQuota=100% ↔ --cpus=1); `CPUQuota=` YALNIZ docker "
        "istemcisini sınırlar. ExecStart'ı yeniden yazan drop-in varsa bayrak orada da.")


CP = DEPLOY / "hindsight" / "hindsight-cp.service"
CP_DROPIN = DEPLOY / "hindsight" / "hindsight-cp.service.d" / "50-vault-yan-dosya.conf"

CPU_OTEN_MUTASYONLAR = [
    ("cpus_silindi", [("  --cpus=1 \\\n", "")], "cpus_yok"),
    ("cpus_iki", [("--cpus=1", "--cpus=2")], "cpus_esit_degil"),
    ("cpus_yarim", [("--cpus=1", "--cpus=0.5")], "cpus_esit_degil"),
    ("cpus_sifir_tavansiz", [("--cpus=1", "--cpus=0")], "cpus_gecersiz"),
    ("cpus_ayrismaz", [("--cpus=1", "--cpus=bir")], "cpus_gecersiz"),
    ("cpus_ikinci", [("--cpus=1", "--cpus=1 --cpus 1")], "cpus_coklu"),
    ("cpu_quota_bayragi_cpus_sayilmaz", [("--cpus=1", "--cpu-quota=100000")], "cpus_yok"),
    ("cpu_shares_cpus_sayilmaz", [("--cpus=1", "--cpu-shares=1024")], "cpus_yok"),
    ("cpuquota_farkli", [("CPUQuota=100%", "CPUQuota=200%")], "cpus_esit_degil"),
    ("cpuquota_sifir", [("CPUQuota=100%", "CPUQuota=0%")], "cpuquota_gecersiz"),
    ("cpuquota_yuzdesiz", [("CPUQuota=100%", "CPUQuota=1")], "cpuquota_gecersiz"),
]


def _cp_bozuk(degisiklikler: list[tuple[str, str]]) -> str:
    metin = CP.read_text(encoding="utf-8")
    for eski, yeni in degisiklikler:
        metin = _bozuk(metin, eski, yeni)
    return metin


@pytest.mark.parametrize("kimlik, degisiklikler, beklenen", CPU_OTEN_MUTASYONLAR, ids=[m[0] for m in CPU_OTEN_MUTASYONLAR])
def test_E2_POZITIF_KONTROL_bozuk_birimde_cpu_denetcisi_OTER(tmp_path, kimlik, degisiklikler, beklenen):
    birim = _sahte(tmp_path, "hindsight-cp", _cp_bozuk(degisiklikler))
    turler = [x["tur"] for x in _cpu_bulgulari([birim])]
    assert beklenen in turler, f"{kimlik}: denetçi ÖTMEDİ: {turler}"


CPU_ESDEGER_YAZIMLAR = [
    ("ayri_jeton", [("--cpus=1", "--cpus 1")]),
    ("ondalik", [("--cpus=1", "--cpus=1.0")]),
    ("yarim_iki_katman", [("--cpus=1", "--cpus=.5"), ("CPUQuota=100%", "CPUQuota=50%")]),
    ("ondalikli_yuzde", [("--cpus=1", "--cpus=1.505"), ("CPUQuota=100%", "CPUQuota=150.5%")]),
    ("cpuquota_yok_cpus_zorunlu_degil", [("CPUQuota=100%\n", "")]),
    ("cpuquota_bos_sifirlama_zorunlu_degil", [("CPUQuota=100%", "CPUQuota=")]),
]


@pytest.mark.parametrize("kimlik, degisiklikler", CPU_ESDEGER_YAZIMLAR, ids=[m[0] for m in CPU_ESDEGER_YAZIMLAR])
def test_E3_NEGATIF_KONTROL_esdeger_yazimda_cpu_denetcisi_SUSAR(tmp_path, kimlik, degisiklikler):
    """Ayrı jetonlu `--cpus 1` v584 `_DEGERLI`deki `--cpus`a dayanır: o küme `--cpus`u kaybederse `1` imaj olur ve
    bu kontrol kırmızıya döner. Bellek denetçisi (A1) de susar — CPU yazımı bellek kuralını bozmaz."""
    birim = _sahte(tmp_path, "hindsight-cp", _cp_bozuk(degisiklikler))
    assert _cpu_bulgulari([birim]) == [], f"{kimlik}: eşdeğer yazımda yanlış alarm: {_cpu_bulgulari([birim])}"
    assert _bulgular([birim]) == [], f"{kimlik}: bellek denetçisi bozuldu: {_bulgular([birim])}"


CPU_DROPIN_MUTASYONLARI = [
    ("dropin_CPUQuota_degistirir", "[Service]\n", "[Service]\nCPUQuota=200%\n", "cpus_esit_degil"),
    ("dropin_ExecStart_cpussuz", "[Service]\n",
     "[Service]\nExecStart=\nExecStart=/usr/bin/docker run --rm --name hindsight-cp --memory=512m img:1.0\n", "cpus_yok"),
]


@pytest.mark.parametrize("kimlik, eski, yeni, beklenen", CPU_DROPIN_MUTASYONLARI,
                         ids=[m[0] for m in CPU_DROPIN_MUTASYONLARI])
def test_E4_POZITIF_KONTROL_drop_in_BIRLESIK_cpu_gorunumunu_bozar_birim_TEMIZ(tmp_path, kimlik, eski, yeni, beklenen):
    """hindsight-cp'nin gerçek drop-in'i ExecStart'a dokunmaz (yalnız ortam dosyası); birleşik hâlin CPU tavanı yine de
    ölçülür — ExecStart'ı ya da kotayı değiştiren bir drop-in yalnız BİRLEŞİK görünümü bozar."""
    birim = _sahte(tmp_path, "hindsight-cp", CP.read_text(encoding="utf-8"),
                   dropin=_bozuk(CP_DROPIN.read_text(encoding="utf-8"), eski, yeni))
    bulgular = _cpu_bulgulari([birim])
    assert beklenen in [x["tur"] for x in bulgular if x["gorunum"] == "birlesik"], f"{kimlik}: {bulgular}"
    assert [x for x in bulgular if x["gorunum"] == "birim"] == [], f"{kimlik}: temel birim bozuk görünüyor: {bulgular}"


def test_E5_POZITIF_KONTROL_gercek_drop_in_ile_BIRLESIK_gorunum_kotayi_TASIR():
    """Gerçek hindsight-cp drop-in'i CPUQuota'yı sıfırlamaz: birleşik görünüm temel birimin kotasını görür (E1'in
    birleşik hâli boş bir kontrol değil)."""
    birlesik = [g for g in _gorunumler(CP) if g.kip == "birlesik"]
    assert len(birlesik) == 1 and birlesik[0].cpu_quota is not None and birlesik[0].cpu_quota[1] == CP, birlesik


def test_E6_yeni_sahte_CPU_kotali_docker_birimi_GERCEK_globlarla_kapsama_girer_ve_OTER(tmp_path):
    """C1'in CPU eşi: glob'un kapsadığı dizine konan YENİ bir CPU kotalı docker birimi liste düzenlenmeden E'ye girer."""
    ansible = tmp_path / "ansible"
    ansible.mkdir()
    yeni = _sahte(tmp_path / "hindsight", "sahte-kotali",
                  "[Service]\nExecStart=/usr/bin/docker run --rm --name sahte-kotali --memory=64m img:1.0\n"
                  "MemoryMax=64M\nCPUQuota=50%\n")
    birimler = _birimler(_defaults()["birim_kaynaklari"], ansible)
    assert yeni.resolve() in birimler, f"yeni birim türetilmiş kapsamda değil: {birimler}"
    assert [(x["birim"], x["tur"]) for x in _cpu_bulgulari(birimler)] == [("sahte-kotali.service", "cpus_yok")]

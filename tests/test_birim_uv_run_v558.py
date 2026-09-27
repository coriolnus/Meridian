"""v558 — TSK-228: birim komut satırında BAYRAKSIZ `uv run` sınıfı (dev grubu venv salınımı, 2026-09-26).

OLAY (Rol-1 ölçümü, dağıtım #67/#68): A1 venv'i HER dağıtımda İKİ KEZ değişiyor, A0 `site.yml`in
"VENV DEĞİŞTİ" uyarısı gürültüye dönüyordu. Zincir: A0 rolü (`venv.yml`) ve dagit `[3]`
`uv sync --frozen {{ uv_sync_bayrak }}` (`--no-dev`) koşar — `uv sync` VARSAYILAN OLARAK EXACT'tir ve dev
grubunun paketlerini KALDIRIR; ardından restart edilen `meridian` / `meridian-barsarchive` birimlerinin
ExecStart'ı bayraksız `uv run …` idi — `uv run` komutu koşmadan önce proje ortamını eşitler ve VARSAYILAN
grupları KURAR (pyproject'te `tool.uv.default-groups` yok → varsayılan küme yalnız `dev`).

ÖLÇÜM (bu tur, Mac, uv 0.11.28, scratchpad'de yalıtılmış örnek proje: ana bağımlılık `iniconfig`, dev
grubu `pluggy`; `--offline`):
    sync --frozen --no-dev             → "Installed 1 package" (iniconfig)
    run true           (bayraksız)     → "Installed 1 package" (pluggy = dev)    ← birimlerin eski hâli
    sync --frozen --no-dev (tekrar)    → "Uninstalled 1 package - pluggy"        ← salınım
    run --no-dev true  (×2)            → çıktı YOK, venv değişmez                 ← SEÇİLEN
    run --no-sync true                 → çıktı YOK                                 ← aday 2
  ana bağımlılık elle kaldırıldıktan sonra (bozuk venv benzetimi):
    run --no-sync python -c 'import iniconfig' → ModuleNotFoundError, rc=1    (ONARMAZ)
    run --no-dev  python -c 'import iniconfig' → "Installed 1 package", rc=0  (onarır; dev geri GELMEZ)

KARAR: `--no-dev` — A0'ın AYNI bayrağı. uv belgesi (`uv help run`, 0.11.28): "When used in a project, the
project environment will be created and updated before invoking the command"; `--no-dev`: "This option is
an alias of `--no-group dev`"; `--exact`: "By default, `uv run` will make the minimum necessary changes to
satisfy the requirements". Yani A0'ın exact `sync --no-dev`inden sonra `run --no-dev` hiçbir şey yapmaz;
dağıtım başına salınım biter.
`--no-sync` REDDEDİLDİ — BEDEL ölçüldü (yukarıda): belge "Avoid syncing the virtual environment. Implies
`--frozen`". Tek-kaynak açısından daha saftır (birim hiçbir grup kararı taşımaz) ama birimlerin bugünkü
KENDİ-KENDİNİ ONARMASINI kaldırır: eksik/bozuk venv'de `Restart=always` worker'ı onarmak yerine ImportError
döngüsüne sokar ve — asıl bedel — son katman alarmı `meridian-fail-notify` de aynı venv'den
`meridian.notify` içe aktarır: venv bozukken alarm da susardı. O davranış değişikliği ayrı bir karardır ve
ayrı ölçüm ister (A1 uv sürümünde `--no-sync` + eksik `.venv`; `~/.cache` izninin o kipte gerekliliği).
`--no-sync` bu yüzden kuralı KARŞILAMAZ; seçilecekse `UV_BEYANI`na gerekçesiyle girer.

SINIF > ÖRNEK: brief iki birim adlandırdı; depo taraması DÖRT buldu (2026-09-26): `meridian` ·
`meridian-barsarchive` · `meridian-fail-notify` (OnFailure; her ateşlemede dev'i geri kurardı) ·
`meridian-backup` (`/bin/sh -c` İÇİNDE, GÜNLÜK timer — iki dağıtım arasında dev'i HER GECE geri kurar; yalnız
brief'in ikisini düzeltmek "VENV DEĞİŞTİ" gürültüsünü bitirmezdi). Dördü de düzeltildi.

TEK KAYNAK: bayrak A0 `defaults/main.yml::uv_sync_bayrak`ta yaşar. Birim dosyaları rol tarafından ŞABLONSUZ
kopyalanır (`birimler.yml` → `ansible.builtin.copy`, `template` DEĞİL), yani birimde literal kopya
KAÇINILMAZ; tek-kaynak yasasının çaresi türetme + AYRIŞMA ÇİVİSİ: aşağıdaki kural bayrağı defaults'tan
OKUR, kendisi literal yazmaz (B2 bunu defaults'u değiştirerek ısırır). `uv_sync_bayrak` bir gün
`--no-default-groups`a yükseltilirse dört birim AYNI değişiklikte güncellenmezse kırmızı.

KURAL (A): depodaki her birim biçimli dosyada ve drop-in'de (kapsam v554 `_kapsam()` — A0 rolünün kurduğu
kümeyi kapsadığı v554 A1'de çivili; tarama kümesi ikinci kez tanımlanmaz) KOMUT yönergelerindeki
(v554 `KOMUT_YONERGELERI`) her proje-eşitleyen uv çağrısı (`ESITLEYEN_ALT_KOMUTLAR`: `run`, `sync` — sınıf
`run`la sınırlı değil, bayraksız `uv sync` aynı salınımı üretir) `uv_sync_bayrak`ı, alt komuttan SONRA ve
çalıştırılan komuttan ÖNCE taşır (komuttan sonraki `--no-dev` komutun argümanıdır, uv'nin DEĞİL). Değilse
ya `UV_BEYANI`nda (dosya, yönerge) anahtarıyla gerekçelidir ya da öter.

ALGILAYICI: değer `\\s ; & | ( ) ' " \\``  ile kelimelere bölünür (böylece `sh -c '…'` gövdesindeki çağrı da
görünür); temel adı `uv` olan kelime (`/home/ubuntu/.local/bin/uv` dahil) bir çağrı başlatır; İLK alt komut
kelimesine kadar olan kelimeler genel seçeneklerdir (`uv --directory /x run` — değerli genel seçenek alt
komutu gizlemez), alt komuttan sonra `-` ile başlayan kelimeler alt komut seçenekleridir (`--`ta durur).

MODELLENMEYEN (bilinçli; hepsi GÜRÜLTÜLÜ yönde ya da adıyla KAPSAM DIŞI):
  · Değer alan bir `run` seçeneği (`--with x`, `--python 3.12`) bayraktan ÖNCE yazılırsa değer kelimesi
    seçenek taramasını durdurur → bayrak görülmez → ÖTER.
  · `Environment=UV_NO_DEV=1` eşdeğeri → ÖTER (ortamdan gelen bayrak komut satırını okuyana görünmez;
    kabul edilmesi kasıtlı olarak reddedildi — beyanla girer).
  · uv ikilisini değişkenle çağırmak (`${UV} run`) → GÖRÜLMEZ (bugün depoda yok, 2026-09-26).
  · Python gövdesinde düz `uv` kelimesi → sahte çağrı sayılabilir → ÖTER.
  · Birim DIŞI uv çağrıları (RUNBOOK'taki elle `uv run` komutları, `bakim_h9.sh`, eski `deploy.sh`) KAPSAM
    DIŞI — TSK-230'da `tests/test_uv_cagri_hijyeni_v566.py` kapsadı (aynı `_beklenen()`, aynı algılayıcı);
    ExecStart'ın çağırdığı betik gövdeleri ölçüldü (2026-09-26): `tick_watchdog.sh`,
    `hindsight-api-baslat.sh`, `taban_orneklem.sh`, vault betikleri `uv` çağırmaz.
  · `uvx` (araç ortamı, proje venv'ine dokunmaz) ölçülmez.
  · Kilit tazeliği ekseni: A0 `sync --frozen`, birim `run` kilidi denetler; pyproject ↔ uv.lock ayrışırsa
    birim yeniden kilitler (uv.lock yazar + ağ). Ayrı sınıf, ayrı karar (TSK-228 raporu) — kapısı TSK-230'da
    kuruldu: CI duman `[0/4]` + dagit `[0b]` `uv lock --check --offline` (v566 E).

A1 uv SÜRÜMÜ BU TURDA ÖLÇÜLMEDİ (ajan A1'e ssh yapmaz): pin `defaults/main.yml::uv_surum` = 0.12.0
(Rol-1 ölçümü 2026-09-08). `--no-dev` `uv run`da 0.11.28'de belgeli; A1'de `uv run --help` ile dağıtımdan
önce Rol-1 ölçer.

TUR 2 — `--frozen` (Rol-1 hükmü 2026-09-27, inceleme §1 artık riski). Brief "A0 ile AYNI semantik" diyor; A0/dagit
`uv sync --frozen {{ uv_sync_bayrak }}` koşar. `--frozen`sız `uv run` kilidi DENETLER: pyproject ↔ uv.lock
ayrışırsa A1'de açılışta uv.lock'u YENİDEN YAZAR + ağa çıkar + A0'ın kurmadığı paketi kurar. Ölçüm (aynı
yalıtılmış proje; pluggy ANA bağımlılığa eklendi, kilit yenilenmedi):
    sync --frozen --no-dev           → "Checked 1 package", kilit d6e4d338… DEĞİŞMEDİ     (A0)
    run --frozen --no-dev true       → çıktı yok, kilit DEĞİŞMEDİ                         (tur 2)
    run --no-dev true                → "Installed 1 package", kilit → a8879b85… YAZILDI   (tur 1 — artık risk)
Bedel (hüküm yanlışsa): bayat kilit bayat bağımlılıkla koşar — A0 bugün TAM OLARAK bunu yapıyor, yeni risk yok.
Kural bu yüzden tek bayraktan bir KÜMEYE genişledi: birim çağrısının eşitleme-semantiği bayrakları
(`ESITLEME_SEMANTIGI`: kilit · grup · extra · kesinlik · kurulum kapsamı) A0'ın `uv sync` görev METNİNİN
(`venv.yml` + dagit `[3]`; `{{ … }}` defaults'tan çözülür) aynı süzgeçten geçmiş kümesine EŞİT olmak zorunda —
iki yönlü: birimde eksik bayrak da (ör. `--frozen` silindi), A0'da olmayan fazla bayrak da (ör. `--all-groups`,
`--no-sync`) öter; A0 metninden `--frozen` silinirse birimler öter (B3). Semantik DIŞI bayraklar (`--quiet`,
`--offline`) serbesttir. SIRA da A0'dan gelir (E1: `uv run --frozen --no-dev` — A0 `sync --frozen <bayrak>`).

Numara v558: ana checkout + worktree'lerde boş (ölçüldü 2026-09-26; v557 tsk226c). Bu dosya hiçbir `state/`
yolu okumaz/yazmaz; sentetik birimler `tmp_path` altında kurulur.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest
import yaml

# Tek-kaynak: birim sözdizimi (yorum + `\\` devamı) v553'te, tarama kapsamı + komut yönergeleri v554'te yaşar.
from tests.test_birim_argv_sir_v554 import KOMUT_YONERGELERI, _goreli, _kapsam
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _yonergeler

KOK = Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy"
ORACLE = DEPLOY / "oracle-a1"
ROL = DEPLOY / "ansible" / "roles" / "meridian_a1"
DEFAULTS = ROL / "defaults" / "main.yml"
#: A0'ın canlı venv'i eşitleyen İKİ görev dosyası (tur 2: `--frozen`in kaynağı bu metinlerdir).
VENV_YML = ROL / "tasks" / "venv.yml"
DAGIT_YML = DEPLOY / "ansible" / "dagit.yml"
#: Birimlerin karşılaştırıldığı KANONİK A0 metni: rolün kendi görevi (dagit `[3]` B0'da ona eşitlenir).
A0_KANONIK = "venv.yml"

#: `uv help` komut listesi (uv 0.11.28, 2026-09-26). Algılayıcı `uv` kelimesinden sonra bu kümeden İLK
#: kelimeye kadar tarar; aradakiler genel seçenek ve değerleridir.
UV_ALT_KOMUTLARI = frozenset({
    "auth", "run", "init", "add", "remove", "version", "sync", "lock", "export", "tree", "format", "check",
    "audit", "tool", "python", "pip", "venv", "build", "publish", "workspace", "cache", "self", "help",
})
#: Proje ortamını VARSAYILAN gruplarla eşitleyen alt komutlar — kuralın ölçtüğü küme.
ESITLEYEN_ALT_KOMUTLAR = frozenset({"run", "sync"})
#: Hem `uv sync` hem `uv run` için belgeli, dev grubunu dışlayan bayraklar (`uv help sync|run`, 0.11.28).
#: `uv_sync_bayrak` bunlardan biri olmak zorunda — yoksa birime kopyalanan şey "dev hariç" anlamı taşımaz.
DEV_HARIC_BAYRAKLAR = frozenset({"--no-dev", "--no-default-groups"})

#: Eşitlemenin NE kuracağını/kilide nasıl davranacağını belirleyen bayraklar (`uv help run|sync`, 0.11.28):
#: kilit · grup · extra · kesinlik · kurulum kapsamı. Birim ↔ A0 kıyası YALNIZ bu süzgeçten geçen bayraklarla
#: yapılır; `--quiet`/`--offline` gibi semantik dışı bayraklar serbesttir. `--exact`/`--inexact` bilerek
#: içeride: `sync` varsayılan exact, `run` varsayılan inexact — biri eklenirse bu bir DAVRANIŞ kararıdır ve
#: beyan ister (gürültülü yön).
ESITLEME_SEMANTIGI = frozenset({
    "--frozen", "--locked", "--no-sync",
    "--no-dev", "--dev", "--only-dev", "--no-default-groups", "--group", "--no-group", "--only-group",
    "--all-groups",
    "--extra", "--all-extras", "--no-extra",
    "--exact", "--inexact",
    "--no-install-project", "--no-install-workspace", "--no-install-local", "--no-install-package",
    "--no-editable",
})

#: (depo-göreli dosya, yönerge) → gerekçe (≥20 karakter). BOŞ başlar (TSK-228).
UV_BEYANI: dict[tuple[str, str], str] = {}

_AYIRICI = re.compile(r"""[\s;&|()'"`]+""")


# ================================================================================================
# Çekirdek — gerçek depo ve sentetik birimler AYNI fonksiyonlardan geçer
# ================================================================================================

def _uv_cagrilari(deger: str) -> list[tuple[str, tuple[str, ...]]]:
    """Komut değerindeki `uv <alt komut>` çağrıları: [(alt komut, uv seçenekleri)].

    Seçenekler = genel seçenekler (alt komuttan önce `-` ile başlayanlar) + alt komut seçenekleri (alt
    komuttan sonra, çalıştırılan komuta ya da `--`a kadar `-` ile başlayanlar)."""
    kelimeler = [k for k in _AYIRICI.split(deger) if k]
    cikti: list[tuple[str, tuple[str, ...]]] = []
    for i, kelime in enumerate(kelimeler):
        if kelime.rsplit("/", 1)[-1] != "uv":
            continue
        j = i + 1
        genel: list[str] = []
        while j < len(kelimeler) and kelimeler[j] not in UV_ALT_KOMUTLARI:
            if kelimeler[j].startswith("-"):
                genel.append(kelimeler[j])
            j += 1
        if j >= len(kelimeler):
            continue  # alt komutsuz `uv` (ör. `uv --version`) — ortamı eşitlemez
        alt = kelimeler[j]
        secenekler: list[str] = []
        j += 1
        while j < len(kelimeler) and kelimeler[j].startswith("-") and kelimeler[j] != "--":
            secenekler.append(kelimeler[j])
            j += 1
        cikti.append((alt, (*genel, *secenekler)))
    return cikti


@dataclasses.dataclass(frozen=True, order=True)
class Ihlal:
    kaynak: str
    yonerge: str
    alt_komut: str
    secenekler: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.kaynak} · {self.yonerge} · uv {self.alt_komut} {' '.join(self.secenekler) or '(seçeneksiz)'}"


def _semantik(secenekler) -> frozenset[str]:
    """Seçeneklerin eşitleme-semantiği kümesi (`--group=dev` → `--group`; semantik dışı atılır)."""
    return frozenset(s.split("=", 1)[0] for s in secenekler if s.split("=", 1)[0] in ESITLEME_SEMANTIGI)


def _uv_tara(dosyalar: list[Path], *, beklenen: frozenset[str], kok: Path = KOK, beyan: dict | None = None
             ) -> tuple[list[Ihlal], set[tuple[str, str]], int]:
    """A kuralı: her eşitleyen çağrının semantik kümesi `beklenen`e EŞİT (iki yönlü). Dönüş: (ihlaller,
    kullanılan beyan anahtarları, görülen eşitleyen çağrı sayısı)."""
    beyan = UV_BEYANI if beyan is None else beyan
    ihlaller: list[Ihlal] = []
    kullanilan: set[tuple[str, str]] = set()
    gorulen = 0
    for p in dosyalar:
        kaynak = _goreli(p, kok)
        for _bolum, anahtar, deger in _yonergeler(p.read_text(encoding="utf-8")):
            if anahtar not in KOMUT_YONERGELERI:
                continue
            for alt, secenekler in _uv_cagrilari(deger):
                if alt not in ESITLEYEN_ALT_KOMUTLAR:
                    continue
                gorulen += 1
                if _semantik(secenekler) == beklenen:
                    continue
                if (kaynak, anahtar) in beyan:
                    kullanilan.add((kaynak, anahtar))
                    continue
                ihlaller.append(Ihlal(kaynak, anahtar, alt, secenekler))
    return sorted(ihlaller), kullanilan, gorulen


def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _bayrak() -> str:
    """A0 rolünün dev-hariç bayrağı (defaults `uv_sync_bayrak`)."""
    return str(_defaults()["uv_sync_bayrak"])


def _sablon_coz(metin: str, degerler: dict) -> str:
    """`{{ ad }}` → defaults değeri; iç içe şablon (`uv_ikili` → `meridian_kullanici`) sabitlenene dek."""
    for _ in range(5):
        yeni = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(degerler.get(m.group(1), m.group(0))), metin)
        if yeni == metin:
            break
        metin = yeni
    return metin


def _komutlar(dugum):
    """YAML ağacındaki her command/shell görevinin komut metni (block/rescue/always dahil, özyinelemeli)."""
    if isinstance(dugum, dict):
        for modul in ("ansible.builtin.command", "command", "ansible.builtin.shell", "shell"):
            arg = dugum.get(modul)
            if isinstance(arg, str):
                yield arg
            elif isinstance(arg, dict) and isinstance(arg.get("cmd"), str):
                yield arg["cmd"]
        for deger in dugum.values():
            yield from _komutlar(deger)
    elif isinstance(dugum, list):
        for oge in dugum:
            yield from _komutlar(oge)


def _a0_sync_bayraklari(metinler: dict[str, str] | None = None) -> dict[str, tuple[str, ...]]:
    """A0'ın canlı venv'i eşitleyen `uv sync` çağrısının seçenekleri, görev METNİNDEN, SIRASIYLA:
    {kaynak: seçenekler}. Her kaynakta TEK `uv sync` çağrısı olmak zorunda (yoksa kaynak belirsiz)."""
    if metinler is None:
        metinler = {"venv.yml": VENV_YML.read_text(encoding="utf-8"),
                    "dagit.yml [3]": DAGIT_YML.read_text(encoding="utf-8")}
    d = _defaults()
    cikti: dict[str, tuple[str, ...]] = {}
    for kaynak, metin in metinler.items():
        cagrilar = [c for cmd in _komutlar(yaml.safe_load(metin))
                    for c in _uv_cagrilari(_sablon_coz(cmd, d)) if c[0] == "sync"]
        assert len(cagrilar) == 1, f"{kaynak}: `uv sync` çağrısı tek değil: {cagrilar} — A0 kaynağı belirsiz"
        cikti[kaynak] = cagrilar[0][1]
    return cikti


def _beklenen() -> frozenset[str]:
    """TEK KAYNAK: birimin taşıması gereken eşitleme-semantiği = A0 rol görevinin `uv sync` bayrakları."""
    return _semantik(_a0_sync_bayraklari()[A0_KANONIK])


def _bicimle(ihlaller) -> str:
    return "\n".join(f"  · {i}" for i in ihlaller)


# ================================================================================================
# A — kural (gerçek depo)
# ================================================================================================

def test_A1_birim_komutunda_BAYRAKSIZ_uv_esitlemesi_YOK():
    beklenen = _beklenen()
    ihlaller, _, _ = _uv_tara(_kapsam(), beklenen=beklenen)
    assert not ihlaller, (
        f"birim komut satırında eşitleme-semantiği A0'dan ({sorted(beklenen)}) AYRIK proje-eşitleyen uv "
        "çağrısı — bayraksız hâli açılışta VARSAYILAN grupları (dev dahil) kurar, `--frozen`sız hâli kilidi "
        "yeniden yazabilir; A0/dagit `uv sync` her dağıtımda geri alır (venv salınımı):\n"
        f"{_bicimle(ihlaller)}\n"
        f"ÇARE: `uv run {' '.join(_a0_sync_bayraklari()[A0_KANONIK])} <komut>` (bayraklar alt komuttan SONRA, "
        "komuttan ÖNCE; kaynak A0 `venv.yml` `uv sync` görev metni + defaults `uv_sync_bayrak`). Meşru durum: "
        "UV_BEYANI'na gerekçesiyle.")


def test_A2_tarama_KOR_DEGIL_depoda_esitleyen_uv_cagrisi_gorulur():
    """Canlı taban: algılayıcı gerçek depoda çağrı GÖRÜYOR (A1 "ihlal yok" demeyi boşta hak etmesin) ve
    brief'in iki birimi bu çağrıların içinde."""
    _, _, gorulen = _uv_tara(_kapsam(), beklenen=_beklenen())
    assert gorulen >= 2, f"depoda yalnız {gorulen} eşitleyen uv çağrısı görüldü — algılayıcı kör olabilir"
    for ad in ("meridian.service", "meridian-barsarchive.service"):
        _, _, n = _uv_tara([ORACLE / ad], beklenen=_beklenen())
        assert n == 1, f"{ad}: ExecStart'ta tek `uv run` beklenirken {n} görüldü — ayrıştırıcı kırık"


# ================================================================================================
# B — tek kaynak ve ayrışma
# ================================================================================================

def test_B0_A0_iki_sync_gorevi_AYNI_semantigi_tasir_ve_bayragi_defaults_tan_alir():
    """Kaynak tek olmalı: rolün `venv.yml`i ile dagit `[3]` aynı eşitleme-semantiğini taşır (biri
    `--frozen`ı bırakırsa "A0 semantiği" iki anlama bölünür ve birimler hangisine eşitlenecek bilinmez)."""
    a0 = _a0_sync_bayraklari()
    kumeler = {k: _semantik(v) for k, v in a0.items()}
    assert len(set(kumeler.values())) == 1, f"A0'ın iki `uv sync` görevi ayrıştı: {kumeler}"
    assert _bayrak() in kumeler[A0_KANONIK], (
        f"A0 `uv sync` metni defaults `uv_sync_bayrak`ı ({_bayrak()!r}) taşımıyor: {a0}")


def test_B1_bayrak_defaults_tan_gelir_ve_DEV_HARIC_semantigi_tasir():
    bayrak = _bayrak()
    assert bayrak in DEV_HARIC_BAYRAKLAR, (
        f"`uv_sync_bayrak` = {bayrak!r} — dev grubunu dışlayan, `uv sync` VE `uv run`da belgeli bir bayrak "
        f"değil ({sorted(DEV_HARIC_BAYRAKLAR)}); birimlere kopyalanan değer A0 ile aynı anlamı taşımaz")


def test_B2_AYRISMA_defaults_degisirse_her_birim_cagrisi_OTER():
    """Çivinin kaynağa BAĞLI olduğunun kanıtı: defaults başka bir dev-hariç bayrağa geçerse (ör.
    `--no-default-groups`a yükseltme) birimler aynı değişiklikte güncellenmedikçe HER çağrı öter."""
    baska = sorted(DEV_HARIC_BAYRAKLAR - {_bayrak()})[0]
    beklenen = (_beklenen() - {_bayrak()}) | {baska}
    ihlaller, _, gorulen = _uv_tara(_kapsam(), beklenen=beklenen)
    assert gorulen and len(ihlaller) == gorulen, (
        f"defaults {baska!r} olsaydı {gorulen} çağrının yalnız {len(ihlaller)}'i ötecekti — birimde "
        "defaults'tan bağımsız bir kabul yolu var")


def test_B3_AYRISMA_A0_gorev_metni_frozen_birakirsa_her_birim_cagrisi_OTER():
    """Kıyas İKİ YÖNLÜ (eşitlik, kapsama DEĞİL): A0 metni `--frozen`ı bırakırsa birimin fazla `--frozen`ı
    da öter — yoksa A0 değiştiğinde birimler sessizce eski semantikte kalırdı."""
    metinler = {"venv.yml": VENV_YML.read_text(encoding="utf-8")}
    assert metinler["venv.yml"].count(" sync --frozen ") == 1, "ön koşul: venv.yml `sync --frozen` taşımıyor"
    metinler["venv.yml"] = metinler["venv.yml"].replace(" sync --frozen ", " sync ")
    beklenen = _semantik(_a0_sync_bayraklari(metinler)["venv.yml"])
    assert "--frozen" not in beklenen and _bayrak() in beklenen, beklenen
    ihlaller, _, gorulen = _uv_tara(_kapsam(), beklenen=beklenen)
    assert gorulen and len(ihlaller) == gorulen, (
        f"A0 `--frozen`sız olsaydı {gorulen} çağrının yalnız {len(ihlaller)}'i ötecekti — kıyas tek yönlü")


# ================================================================================================
# C — beyan hijyeni
# ================================================================================================

def test_C1_UV_BEYANI_gerekceli_ve_curumez():
    for anahtar, gerekce in UV_BEYANI.items():
        assert isinstance(anahtar, tuple) and len(anahtar) == 2, anahtar
        assert anahtar[1] in KOMUT_YONERGELERI, f"{anahtar}: komut yönergesi değil"
        assert len(gerekce.strip()) >= 20, f"{anahtar}: gerekçe kısa"
    _, kullanilan, _ = _uv_tara(_kapsam(), beklenen=_beklenen())
    curuk = sorted(set(UV_BEYANI) - kullanilan)
    assert not curuk, f"çürük beyan (ayrık çağrı artık yok — SİL): {curuk}"


# ================================================================================================
# D — pozitif kontrol: algılayıcı ve dosya düzeyi
# ================================================================================================

_B = "--no-dev"

# (kimlik, komut değeri, beklenen [(alt komut, bayrak var mı)])
ALGILAYICI_DURUMLARI = [
    ("yol_onekli_bayraksiz", "/home/ubuntu/.local/bin/uv run uvicorn m.api:app --port 8080", [("run", False)]),
    ("yol_onekli_bayrakli", f"/home/ubuntu/.local/bin/uv run {_B} uvicorn m.api:app", [("run", True)]),
    ("ciplak_uv", "uv run python -m meridian.barsarchive", [("run", False)]),
    ("sh_c_govdesinde_bayraksiz",
     """/bin/sh -c 'ok=1; if [ -s db ]; then uv run python -c "import sys" db.yedek || ok=0; fi; tar -czf x'""",
     [("run", False)]),
    ("sh_c_govdesinde_bayrakli",
     f"""/bin/sh -c 'ok=1; if [ -s db ]; then uv run {_B} python -c "import sys" db.yedek || ok=0; fi'""",
     [("run", True)]),
    ("bayrak_KOMUTTAN_SONRA_komutundur", f"uv run python -m x {_B}", [("run", False)]),
    ("bayrak_cift_tireden_sonra_komutundur", f"uv run -- python {_B}", [("run", False)]),
    ("genel_secenek_once", f"uv --quiet run {_B} python", [("run", True)]),
    ("degerli_genel_secenek_alt_komutu_GIZLEMEZ", "uv --directory /opt/meridian run python", [("run", False)]),
    ("birden_cok_secenek", f"uv run --frozen {_B} python", [("run", True)]),
    ("sync_bayraksiz", "uv sync --frozen", [("sync", False)]),
    ("sync_bayrakli", f"uv sync --frozen {_B}", [("sync", True)]),
    ("iki_cagri_biri_bayraksiz", f"/bin/sh -c 'uv run {_B} a && uv run b'", [("run", True), ("run", False)]),
    ("uvicorn_uv_DEGIL", "/opt/meridian/.venv/bin/uvicorn meridian.api:app", []),
    ("venv_python_uv_DEGIL", "/opt/meridian/.venv/bin/python -m meridian.learn_run", []),
    ("uvx_uv_DEGIL", "uvx ruff check", []),
    ("alt_komutsuz_uv", "uv --version", []),
    ("esitlemeyen_alt_komut_gorulur_ama_esitlemez", "uv pip list", [("pip", False)]),
]


@pytest.mark.parametrize("kimlik, deger, beklenen", ALGILAYICI_DURUMLARI,
                         ids=[d[0] for d in ALGILAYICI_DURUMLARI])
def test_D1_pozitif_kontrol_ALGILAYICI(kimlik, deger, beklenen):
    bulunan = [(alt, _B in secenekler) for alt, secenekler in _uv_cagrilari(deger)]
    assert bulunan == beklenen, f"{kimlik}: {_uv_cagrilari(deger)}"


def _birim_kur(tmp_path: Path, govde: str, dropinler: dict[str, str] | None = None) -> list[Path]:
    birim = tmp_path / "ornek.service"
    birim.write_text(f"[Unit]\nDescription=sentetik\n\n[Service]\nUser=ubuntu\n{govde}\n", encoding="utf-8")
    dosyalar = [birim]
    if dropinler:
        d = tmp_path / "ornek.service.d"
        d.mkdir()
        for ad, metin in sorted(dropinler.items()):
            (d / ad).write_text(metin, encoding="utf-8")
            dosyalar.append(d / ad)
    return dosyalar


# (kimlik, birim gövdesi, drop-in'ler, beklenen [(kaynak adı, yönerge)])
DOSYA_DURUMLARI = [
    ("bayraksiz_ExecStart_OTER", "ExecStart=/home/ubuntu/.local/bin/uv run uvicorn a:b", None,
     [("ornek.service", "ExecStart")]),
    ("bayrakli_ExecStart_temiz", f"ExecStart=/home/ubuntu/.local/bin/uv run {_B} uvicorn a:b", None, []),
    ("yorum_satiri_SAYILMAZ", f"# ExecStart=uv run eski-bicim\nExecStart=uv run {_B} x", None, []),
    ("ters_bolu_devami_birlestirir", "ExecStart=/bin/sh -c 'true; \\\n  uv run x'", None,
     [("ornek.service", "ExecStart")]),
    ("ExecStartPre_de_olculur", f"ExecStartPre=uv sync --frozen\nExecStart=uv run {_B} x", None,
     [("ornek.service", "ExecStartPre")]),
    ("dropin_ExecStart_sifirlayip_bayraksiz_yazar", f"ExecStart=uv run {_B} x",
     {"50-x.conf": "[Service]\nExecStart=\nExecStart=uv run x\n"},
     [("ornek.service.d/50-x.conf", "ExecStart")]),
    ("komut_olmayan_yonerge_olculmez", "Environment=NOT=uv run x\nExecStart=/bin/true", None, []),
    ("no_sync_kurali_KARSILAMAZ", "ExecStart=uv run --no-sync x", None, [("ornek.service", "ExecStart")]),
]


@pytest.mark.parametrize("kimlik, govde, dropinler, beklenen", DOSYA_DURUMLARI,
                         ids=[d[0] for d in DOSYA_DURUMLARI])
def test_D2_pozitif_kontrol_DOSYA_duzeyi(tmp_path, kimlik, govde, dropinler, beklenen):
    dosyalar = _birim_kur(tmp_path, govde, dropinler)
    ihlaller, _, _ = _uv_tara(dosyalar, beklenen=frozenset({_B}), kok=tmp_path, beyan={})
    assert [(i.kaynak, i.yonerge) for i in ihlaller] == beklenen, f"{kimlik}:\n{_bicimle(ihlaller)}"


def test_D3_beyan_yalniz_ADI_gecen_dosya_ve_yonergeyi_susturur(tmp_path):
    dosyalar = _birim_kur(tmp_path, "ExecStartPre=uv run a\nExecStart=uv run b")
    beyan = {("ornek.service", "ExecStart"): "sentetik: bilinçli bayraksız çağrı gerekçesi"}
    ihlaller, kullanilan, gorulen = _uv_tara(dosyalar, beklenen=frozenset({_B}), kok=tmp_path, beyan=beyan)
    assert gorulen == 2
    assert [(i.kaynak, i.yonerge) for i in ihlaller] == [("ornek.service", "ExecStartPre")]
    assert kullanilan == {("ornek.service", "ExecStart")}


_F = "--frozen"

# (kimlik, komut, beklenen semantik (A0 kümesi), ihlal var mı)
SEMANTIK_DURUMLARI = [
    ("tam_esit_temiz", f"uv run {_F} {_B} x", {_F, _B}, False),
    ("sira_serbest", f"uv run {_B} {_F} x", {_F, _B}, False),
    ("eksik_frozen_OTER", f"uv run {_B} x", {_F, _B}, True),
    ("fazla_grup_OTER", f"uv run {_F} {_B} --all-groups x", {_F, _B}, True),
    ("locked_frozen_yerine_OTER", f"uv run --locked {_B} x", {_F, _B}, True),
    ("no_sync_frozen_yerine_OTER", f"uv run --no-sync {_B} x", {_F, _B}, True),
    ("esittirli_grup_normalize_OTER", f"uv run {_F} {_B} --group=dev x", {_F, _B}, True),
    ("semantik_disi_bayrak_serbest", f"uv run --quiet {_F} {_B} --offline x", {_F, _B}, False),
    ("A0_frozensiz_ise_fazla_frozen_OTER", f"uv run {_F} {_B} x", {_B}, True),
    ("exact_davranis_karari_OTER", f"uv run {_F} {_B} --exact x", {_F, _B}, True),
]


@pytest.mark.parametrize("kimlik, komut, beklenen, oter", SEMANTIK_DURUMLARI,
                         ids=[d[0] for d in SEMANTIK_DURUMLARI])
def test_D4_pozitif_kontrol_SEMANTIK_ESITLIGI_iki_yonlu(tmp_path, kimlik, komut, beklenen, oter):
    dosyalar = _birim_kur(tmp_path, f"ExecStart={komut}")
    ihlaller, _, gorulen = _uv_tara(dosyalar, beklenen=frozenset(beklenen), kok=tmp_path, beyan={})
    assert gorulen == 1 and bool(ihlaller) is oter, f"{kimlik}: {_bicimle(ihlaller)}"


def test_D5_A0_metin_ayristiricisi_sablonu_cozer_ve_TEK_sync_ister():
    """`_a0_sync_bayraklari` sentetik görev metinleriyle: şablon defaults'tan çözülür, sıra korunur; iki
    `uv sync` (kaynak belirsiz) ya da hiç yok → açık hata (sessiz boş küme DEĞİL)."""
    tek = ('- name: s\n  ansible.builtin.command:\n    cmd: "{{ uv_ikili }} sync --frozen {{ uv_sync_bayrak }}"\n')
    assert _a0_sync_bayraklari({"x": tek})["x"] == ("--frozen", _bayrak())
    blok = ('- hosts: h\n  tasks:\n    - block:\n        - ansible.builtin.command:\n'
            '            cmd: "{{ uv_ikili }} sync --locked {{ uv_sync_bayrak }}"\n')
    assert _a0_sync_bayraklari({"x": blok})["x"] == ("--locked", _bayrak())
    for kotu in (tek + tek.replace("- name: s", "- name: t"), "- name: s\n  ansible.builtin.debug:\n    msg: x\n"):
        with pytest.raises(AssertionError, match="tek değil"):
            _a0_sync_bayraklari({"x": kotu})


# ================================================================================================
# E — TSK-228 örneği: brief'in iki birimi, A0'ın AYNI ikilisi ve AYNI bayrakları AYNI sırayla
# ================================================================================================

@pytest.mark.parametrize("ad", ["meridian.service", "meridian-barsarchive.service"])
def test_E1_ExecStart_A0_uv_ikilisini_ve_bayraklarini_ILK_run_secenekleri_olarak_tasir(ad):
    d = _defaults()
    uv_ikili = _sablon_coz(str(d["uv_ikili"]), d)
    assert "{{" not in uv_ikili, f"uv_ikili çözülemedi: {uv_ikili!r}"
    exec_start = [v for b, a, v in _yonergeler((ORACLE / ad).read_text(encoding="utf-8"))
                  if b == "Service" and a == "ExecStart"]
    assert len(exec_start) == 1, f"{ad}: ExecStart tek değil: {exec_start}"
    a0 = [s for s in _a0_sync_bayraklari()[A0_KANONIK] if s.split("=", 1)[0] in ESITLEME_SEMANTIGI]
    beklenen_bas = f"{uv_ikili} run {' '.join(a0)} "
    assert exec_start[0].startswith(beklenen_bas), (
        f"{ad}: ExecStart `{beklenen_bas}…` ile başlamıyor — A0'ın venv'i eşitlediği ikili/bayraklar ile birimin "
        f"koştuğu ayrıştı: {exec_start[0][:90]!r}")

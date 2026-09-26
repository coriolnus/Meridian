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
    DIŞI; ExecStart'ın çağırdığı betik gövdeleri ölçüldü (2026-09-26): `tick_watchdog.sh`,
    `hindsight-api-baslat.sh`, `taban_orneklem.sh`, vault betikleri `uv` çağırmaz.
  · `uvx` (araç ortamı, proje venv'ine dokunmaz) ölçülmez.
  · Kilit tazeliği ekseni: A0 `sync --frozen`, birim `run` kilidi denetler; pyproject ↔ uv.lock ayrışırsa
    birim yeniden kilitler (uv.lock yazar + ağ). Ayrı sınıf, ayrı karar (TSK-228 raporu).

A1 uv SÜRÜMÜ BU TURDA ÖLÇÜLMEDİ (ajan A1'e ssh yapmaz): pin `defaults/main.yml::uv_surum` = 0.12.0
(Rol-1 ölçümü 2026-09-08). `--no-dev` `uv run`da 0.11.28'de belgeli; A1'de `uv run --help` ile dağıtımdan
önce Rol-1 ölçer.

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
DEFAULTS = DEPLOY / "ansible" / "roles" / "meridian_a1" / "defaults" / "main.yml"

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


def _uv_tara(dosyalar: list[Path], *, bayrak: str, kok: Path = KOK, beyan: dict | None = None
             ) -> tuple[list[Ihlal], set[tuple[str, str]], int]:
    """A kuralı. Dönüş: (ihlaller, kullanılan beyan anahtarları, görülen eşitleyen çağrı sayısı)."""
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
                if bayrak in secenekler:
                    continue
                if (kaynak, anahtar) in beyan:
                    kullanilan.add((kaynak, anahtar))
                    continue
                ihlaller.append(Ihlal(kaynak, anahtar, alt, secenekler))
    return sorted(ihlaller), kullanilan, gorulen


def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _bayrak() -> str:
    """TEK KAYNAK: birimlerin taşıması gereken bayrak A0 rolünün defaults'undan okunur."""
    return str(_defaults()["uv_sync_bayrak"])


def _bicimle(ihlaller) -> str:
    return "\n".join(f"  · {i}" for i in ihlaller)


# ================================================================================================
# A — kural (gerçek depo)
# ================================================================================================

def test_A1_birim_komutunda_BAYRAKSIZ_uv_esitlemesi_YOK():
    ihlaller, _, _ = _uv_tara(_kapsam(), bayrak=_bayrak())
    assert not ihlaller, (
        f"birim komut satırında `{_bayrak()}` taşımayan proje-eşitleyen uv çağrısı — açılışta VARSAYILAN "
        "grupları (dev dahil) kurar, A0/dagit `uv sync --frozen` her dağıtımda kaldırır (venv salınımı):\n"
        f"{_bicimle(ihlaller)}\n"
        f"ÇARE: `uv run {_bayrak()} <komut>` (bayrak alt komuttan SONRA, komuttan ÖNCE; değer A0 "
        "`defaults/main.yml::uv_sync_bayrak`). Meşru durum: UV_BEYANI'na gerekçesiyle.")


def test_A2_tarama_KOR_DEGIL_depoda_esitleyen_uv_cagrisi_gorulur():
    """Canlı taban: algılayıcı gerçek depoda çağrı GÖRÜYOR (A1 "ihlal yok" demeyi boşta hak etmesin) ve
    brief'in iki birimi bu çağrıların içinde."""
    _, _, gorulen = _uv_tara(_kapsam(), bayrak=_bayrak())
    assert gorulen >= 2, f"depoda yalnız {gorulen} eşitleyen uv çağrısı görüldü — algılayıcı kör olabilir"
    for ad in ("meridian.service", "meridian-barsarchive.service"):
        _, _, n = _uv_tara([ORACLE / ad], bayrak=_bayrak())
        assert n == 1, f"{ad}: ExecStart'ta tek `uv run` beklenirken {n} görüldü — ayrıştırıcı kırık"


# ================================================================================================
# B — tek kaynak ve ayrışma
# ================================================================================================

def test_B1_bayrak_defaults_tan_gelir_ve_DEV_HARIC_semantigi_tasir():
    bayrak = _bayrak()
    assert bayrak in DEV_HARIC_BAYRAKLAR, (
        f"`uv_sync_bayrak` = {bayrak!r} — dev grubunu dışlayan, `uv sync` VE `uv run`da belgeli bir bayrak "
        f"değil ({sorted(DEV_HARIC_BAYRAKLAR)}); birimlere kopyalanan değer A0 ile aynı anlamı taşımaz")


def test_B2_AYRISMA_defaults_degisirse_her_birim_cagrisi_OTER():
    """Çivinin kaynağa BAĞLI olduğunun kanıtı: defaults başka bir dev-hariç bayrağa geçerse (ör.
    `--no-default-groups`a yükseltme) birimler aynı değişiklikte güncellenmedikçe HER çağrı öter."""
    baska = sorted(DEV_HARIC_BAYRAKLAR - {_bayrak()})[0]
    ihlaller, _, gorulen = _uv_tara(_kapsam(), bayrak=baska)
    assert gorulen and len(ihlaller) == gorulen, (
        f"defaults {baska!r} olsaydı {gorulen} çağrının yalnız {len(ihlaller)}'i ötecekti — birimde "
        "defaults'tan bağımsız bir kabul yolu var")


# ================================================================================================
# C — beyan hijyeni
# ================================================================================================

def test_C1_UV_BEYANI_gerekceli_ve_curumez():
    for anahtar, gerekce in UV_BEYANI.items():
        assert isinstance(anahtar, tuple) and len(anahtar) == 2, anahtar
        assert anahtar[1] in KOMUT_YONERGELERI, f"{anahtar}: komut yönergesi değil"
        assert len(gerekce.strip()) >= 20, f"{anahtar}: gerekçe kısa"
    _, kullanilan, _ = _uv_tara(_kapsam(), bayrak=_bayrak())
    curuk = sorted(set(UV_BEYANI) - kullanilan)
    assert not curuk, f"çürük beyan (bayraksız çağrı artık yok — SİL): {curuk}"


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
    ihlaller, _, _ = _uv_tara(dosyalar, bayrak=_B, kok=tmp_path, beyan={})
    assert [(i.kaynak, i.yonerge) for i in ihlaller] == beklenen, f"{kimlik}:\n{_bicimle(ihlaller)}"


def test_D3_beyan_yalniz_ADI_gecen_dosya_ve_yonergeyi_susturur(tmp_path):
    dosyalar = _birim_kur(tmp_path, "ExecStartPre=uv run a\nExecStart=uv run b")
    beyan = {("ornek.service", "ExecStart"): "sentetik: bilinçli bayraksız çağrı gerekçesi"}
    ihlaller, kullanilan, gorulen = _uv_tara(dosyalar, bayrak=_B, kok=tmp_path, beyan=beyan)
    assert gorulen == 2
    assert [(i.kaynak, i.yonerge) for i in ihlaller] == [("ornek.service", "ExecStartPre")]
    assert kullanilan == {("ornek.service", "ExecStart")}


# ================================================================================================
# E — TSK-228 örneği: brief'in iki birimi, A0'ın AYNI ikilisi ve AYNI bayrağı
# ================================================================================================

@pytest.mark.parametrize("ad", ["meridian.service", "meridian-barsarchive.service"])
def test_E1_ExecStart_A0_uv_ikilisini_ve_bayragini_ILK_run_secenegi_olarak_tasir(ad):
    d = _defaults()
    uv_ikili = str(d["uv_ikili"]).replace("{{ meridian_kullanici }}", str(d["meridian_kullanici"]))
    assert "{{" not in uv_ikili, f"uv_ikili çözülemedi: {uv_ikili!r}"
    exec_start = [v for b, a, v in _yonergeler((ORACLE / ad).read_text(encoding="utf-8"))
                  if b == "Service" and a == "ExecStart"]
    assert len(exec_start) == 1, f"{ad}: ExecStart tek değil: {exec_start}"
    beklenen_bas = f"{uv_ikili} run {_bayrak()} "
    assert exec_start[0].startswith(beklenen_bas), (
        f"{ad}: ExecStart `{beklenen_bas}…` ile başlamıyor — A0'ın venv'i eşitlediği ikili/bayrak ile birimin "
        f"koştuğu ayrıştı: {exec_start[0][:80]!r}")

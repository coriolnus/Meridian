"""v570 — TSK-238 (c): A1 kabuk ortamı — A0 rolü `/etc/environment`e `UV_FROZEN=1` + `UV_NO_DEV=1` yazar.

SORUN. v558 birimleri, v566 metin yüzeyini (betik · elle kılavuz · ileti) A0 semantiğine (`uv sync --frozen
--no-dev`) çekti. Ama bir öğüt unutulursa ya da operatör A1'de elle bayraksız `uv run` yazarsa aynı hasar
doğar: dev grubu geri kurulur, bayat kilit yeniden yazılır. İkinci katman: kabuğun KENDİSİ A0 semantiğini
taşısın.

ROL-1 KARARI (brief, 2026-09-27; kaynak: A1 ölçümü + hafıza: benzer kayıt yok). A1 ölçümü 12:3xZ: ssh
komutunda `UV_NO_DEV`/`UV_FROZEN` YOK; `~/.bashrc` etkileşimsiz kabukta erken döner (oraya yazmak ssh
komutlarını KAPSAMAZ); `/etc/pam.d/sshd` `pam_env` kullanır → `/etc/environment` ssh oturumlarına
(etkileşimsiz komut dahil) uygulanır; dosya bugün 1 satır; systemd birimleri onu OKUMAZ (birimler zaten
bayraklı, v558). Rol iki satırı `lineinfile` ile İDEMPOTENT ekler — öteki satırlara dokunmaz, sahip/izin
korunur.

UV BELGESİ (uydurma yok — İKİ kaynak):
  · uv 0.12.0 (A1 pini) KAYNAĞI, tag 0.12.0, `gh api …/contents?ref=0.12.0` (diske yazılmadı):
    `crates/uv-static/src/env_vars.rs` — "UV_FROZEN: Equivalent to the `--frozen` command-line argument",
    "UV_NO_DEV: Equivalent to the `--no-dev` command-line argument", "UV_LOCKED: Equivalent to the
    `--locked`…"; `crates/uv-settings/src/lib.rs` `EnvFlag::new(EnvVars::UV_FROZEN|UV_NO_DEV)`;
    `crates/uv/src/settings.rs::RunSettings/SyncSettings` bayrağı CLI ∪ ortamdan çözer
    (`resolve_flag(frozen, "frozen", environment.frozen)`).
  · uv 0.11.28 (yerel) `uv help run|sync`: `--no-dev … [env: UV_NO_DEV=]`, `--frozen … [env: UV_FROZEN=]`
    — T1b bunu GERÇEK ikiliden okur (0.12.0 eşlemesiyle ayrışırsa öter).

DAVRANIŞ ÖLÇÜMÜ (bu tur, uv 0.11.28, yalıtılmış proje + depo kopyası, `--offline`, BOŞ önbellek):
  · ortam altında bayraksız `uv run true` → dev grubu KURULMAZ; pyproject ↔ kilit ayrışıkken kilit
    YAZILMAZ (sha d6e4d338 sabit) — bayraksızı `run --no-dev` kilidi a8879b85'e yeniden yazdı.
  · depo kopyası `uv sync --dry-run`: ortamsız 89 satır (+pytest, +mutmut), ortamla 43 (dev yok);
    bayat kopyada ortamsız rc 1 (çözümleme ağ ister), ortamla rc 0 (kilit olduğu gibi). T5 bunu koşar.

BEDEL (Bedel yasası — ne KAYBEDİLİR; ölçüldü + 0.12.0 kaynağı):
  · `UV_FROZEN=1` altında `uv lock --check` KÖRLEŞİR: yalnız geçerlilik denetler, bayat kilitte rc 0 +
    uyarı ("only checked for validity … because `UV_FROZEN=1` was provided"). 0.12.0 `commands/project/
    lock.rs`: `if let Some(frozen_source) = frozen { LockMode::Frozen }` `--check`ten ÖNCE gelir.
  · `uv run|sync --locked` rc 2 ile reddedilir ("cannot be used with `UV_FROZEN`"; 0.12.0
    `check_conflicts(locked, frozen)`).
  · `UV_NO_DEV=1` altında `uv sync --group dev` dev'i KURMAZ (`--no-group` her zaman kazanır); açık
    `--dev` ise ortamı ezer (kurar) — A1'de dev kurulmaz kararıyla aynı yön.
  Kilit tazeliği kapıları A1'de KOŞMAZ: dagit `[0b]` Play 1 (localhost), CI dumanı GitHub koşucusu. T4
  bunu çiviler: A1'e giden yüzeyde `--locked` ya da `uv lock --check` doğarsa öter (kör kapı sessiz olurdu).

TEK KAYNAK. Adlar/değerler rol defaults `uv_kabuk_ortami`nda; görev literal ad taşımaz (T2). Ad → bayrak
eşlemesi uv belgesinden (`ORTAM_BAYRAGI`, 0.12.0); küme A0 `venv.yml` `uv sync` görev metninden (v558
`_beklenen()`) — `uv_sync_bayrak` değişirse (ör. `--no-default-groups`) bu sözlük AYNI değişiklikte
güncellenmezse T1 öter (T1c ısırır).

T3 GERÇEK Ansible modülünü (`ansible` ad-hoc, `ansible.builtin.lineinfile`, `-c local`) tmp dosyada
koşar — `ansible-playbook` DEĞİL, A1'e bağlantı YOK. Kuru koşum (`--check --diff`) yalnız iki satır ekler;
gerçek koşum idempotent; öteki satır ve dosya modu korunur; aynı adın eski ataması tekilleşir.

Numara v570: ana checkout + worktree'lerde boş (ölçüldü 2026-09-27; v569 paralel ajanın). `state/`
okumaz/yazmaz.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import jinja2
import pytest
import yaml

from tests.test_ansible_dagit_v452 import _ansible_ikili, _dagit_yml, _komut_metni, _play_gorevleri
from tests.test_birim_uv_run_v558 import (
    DEV_HARIC_BAYRAKLAR,
    _bayrak,
    _beklenen,
    _defaults,
    _komutlar,
    _sablon_coz,
    _semantik,
    _uv_cagrilari,
)
from tests.test_uv_cagri_hijyeni_v566 import (
    ELLE_RUNBOOK,
    _UV_DEGISKEN,
    _kabuk_parcalari,
    _md_parcalari,
    _sha,
    _uv_ikili,
)

KOK = Path(__file__).resolve().parent.parent
ROL = KOK / "deploy" / "ansible" / "roles" / "meridian_a1"
GOREVLER = ROL / "tasks"
ORTAM_DOSYASI = "/etc/environment"
ORTAM_DEGISKENI = "uv_kabuk_ortami"

#: uv ortam değişkeni → eşdeğer komut satırı bayrağı. KAYNAK: uv 0.12.0 (A1 pini)
#: `crates/uv-static/src/env_vars.rs` ("Equivalent to the `--…` command-line argument"). Yalnız run/sync
#: için belgeli, ölçülmüş üçü; yeni bir ad eklemek belge okumasıyla olur (uydurma yasağı).
ORTAM_BAYRAGI = {"UV_FROZEN": "--frozen", "UV_NO_DEV": "--no-dev", "UV_LOCKED": "--locked"}
#: uv'nin boolish ayrıştırıcısının "açık" değerleri (clap BoolishValueParser; ölçülen: "1").
DOGRU_DEGERLER = frozenset({"1", "true", "yes", "on", "y", "t"})


def _ortam() -> dict[str, str]:
    deger = _defaults().get(ORTAM_DEGISKENI)
    assert isinstance(deger, dict) and deger, f"defaults `{ORTAM_DEGISKENI}` sözlük değil/boş: {deger!r}"
    return {str(k): str(v) for k, v in deger.items()}


def _ortam_semantigi(ortam: dict[str, str]) -> frozenset[str]:
    bilinmeyen = sorted(set(ortam) - set(ORTAM_BAYRAGI))
    assert not bilinmeyen, f"uv belgesinde eşdeğer bayrağı ölçülmemiş ad(lar): {bilinmeyen}"
    yanlis = {k: v for k, v in ortam.items() if v.lower() not in DOGRU_DEGERLER}
    assert not yanlis, f"değer boolish-doğru değil (bayrak AÇILMAZ): {yanlis}"
    return _semantik(ORTAM_BAYRAGI[k] for k in ortam)


# ================================================================================================
# T1 — semantik A0 ile EŞİT, eşleme uv'den
# ================================================================================================

def test_T1_kabuk_ortami_A0_uv_sync_semantigine_ESIT():
    ortam, beklenen = _ortam(), _beklenen()
    assert _ortam_semantigi(ortam) == beklenen, (
        f"A1 kabuk ortamı {ortam} → {sorted(_ortam_semantigi(ortam))} ≠ A0 `uv sync` semantiği {sorted(beklenen)} "
        "— venv.yml/uv_sync_bayrak değiştiyse defaults `uv_kabuk_ortami` AYNI değişiklikte güncellenir")


def test_T1b_adlar_GERCEK_uv_belgesinde_run_ve_sync_icin_var():
    """Yerel uv'nin `help run|sync` çıktısı her adı `[env: AD=]` olarak taşır (ad uydurma değil).
    BAYRAK EŞLEMESİ bu çıktıdan OKUNMAZ — ölçüldü (uv 0.11.28): `help run`da `[env: UV_FROZEN=]`
    satırı `--frozen` bloğunun değil sonraki `--script` bloğunun altında basılıyor (yardım biçimleyici
    kayması; davranış değil: ortam altında `uv run true` betik sayılmadı, normal koştu). Eşlemenin
    kaynağı 0.12.0 kaynağıdır (`ORTAM_BAYRAGI`); DAVRANIŞI T5a (UV_NO_DEV → dev grubu yok) ve T5b
    (UV_FROZEN → bayat kilit çözülmez) gerçek ikiliyle ölçer."""
    ikili = _uv_ikili()
    for alt in ("run", "sync"):
        r = subprocess.run([ikili, "help", alt], capture_output=True, text=True, timeout=60,
                           env={k: v for k, v in os.environ.items() if not k.startswith("UV_")})
        assert r.returncode == 0, r.stderr
        for ad in _ortam():
            assert f"[env: {ad}=]" in r.stdout, f"`uv help {alt}` `[env: {ad}=]` taşımıyor — ad belgede yok"


def test_T1c_AYRISMA_uv_sync_bayragi_degisirse_T1_OTER():
    """Kıyasın A0'a BAĞLI olduğunun kanıtı: A0 başka bir dev-hariç bayrağa geçseydi bugünkü ortam
    sözlüğü eşitliği bozardı (sözlük literal bir kopya değil, A0 ile kıyaslanan bir türevdir)."""
    baska = sorted(DEV_HARIC_BAYRAKLAR - {_bayrak()})[0]
    yeni = (_beklenen() - {_bayrak()}) | {baska}
    assert _ortam_semantigi(_ortam()) != yeni


# ================================================================================================
# T2 — görev biçimi: tek kaynak, satır düzeyi, izin korunur
# ================================================================================================

def _ortam_gorevleri() -> list[tuple[Path, dict]]:
    cikti = []
    for p in sorted(GOREVLER.glob("*.yml")):
        for g in yaml.safe_load(p.read_text(encoding="utf-8")) or []:
            if isinstance(g, dict) and ORTAM_DOSYASI in yaml.safe_dump(g, allow_unicode=True):
                cikti.append((p, g))
    return cikti


def _tek_gorev() -> dict:
    bulunan = _ortam_gorevleri()
    assert len(bulunan) == 1, f"rolde `{ORTAM_DOSYASI}`e dokunan tek görev beklenirdi: {[(p.name, g.get('name')) for p, g in bulunan]}"
    return bulunan[0][1]


def _satir_argumanlari(anahtar: str, deger: str) -> dict:
    """Görevin `lineinfile` argümanlarını bir öğe için ÇÖZER (Jinja, `item` = dict2items öğesi)."""
    args = _tek_gorev()["ansible.builtin.lineinfile"]
    ortam = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=False)
    oge = {"key": anahtar, "value": deger}
    return {k: (ortam.from_string(v).render(item=oge) if isinstance(v, str) else v) for k, v in args.items()}


def test_T2_gorev_lineinfile_TEK_KAYNAKTAN_dongu_ve_izin_KORUNUR():
    g = _tek_gorev()
    assert "ansible.builtin.lineinfile" in g, (
        f"`{ORTAM_DOSYASI}` görevi lineinfile değil: {sorted(g)} — copy/template dosyanın TAMAMINI yazar "
        "(A1'deki bugünkü satır ve ileride elle eklenen satır silinirdi)")
    assert str(g.get("loop", "")).replace(" ", "") == f"{{{{{ORTAM_DEGISKENI}|dict2items}}}}", (
        f"döngü defaults `{ORTAM_DEGISKENI}`ten gelmiyor: {g.get('loop')!r}")
    dokum = yaml.safe_dump(g, allow_unicode=True)
    literal = [ad for ad in (*ORTAM_BAYRAGI, *_ortam()) if ad in dokum]
    assert not literal, f"görev literal ad taşıyor (ikinci kaynak): {literal}"
    args = g["ansible.builtin.lineinfile"]
    assert args.get("path") == ORTAM_DOSYASI
    assert args.get("state", "present") == "present"
    yasak = sorted({"owner", "group", "mode", "create", "backrefs"} & set(args))
    assert not yasak, f"izin/sahip/yaratma argümanı var ({yasak}) — mevcut dosyanın sahip/izni KORUNMAZ"
    for ad, deger in _ortam().items():
        cozulen = _satir_argumanlari(ad, deger)
        assert cozulen["line"] == f"{ad}={deger}", cozulen


# (kimlik, satır, regexp eşleşmeli mi) — regexp YALNIZ aynı adın atamasını yakalar
REGEXP_DURUMLARI = [
    ("ayni_ad_farkli_deger", "{ad}=0", True),
    ("ayni_ad_ayni_deger", "{ad}=1", True),
    ("export_onekli", "export {ad}=0", True),
    ("bosluklu", "  {ad}=0", True),
    ("onekli_baska_ad", "X{ad}=1", False),
    ("sonekli_baska_ad", "{ad}_X=1", False),
    ("yorum_satiri", "# {ad}=1", False),
    ("PATH", 'PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"', False),
]


@pytest.mark.parametrize("kimlik, sablon, eslesmeli", REGEXP_DURUMLARI, ids=[d[0] for d in REGEXP_DURUMLARI])
def test_T2b_regexp_YALNIZ_ayni_adin_atamasini_yakalar(kimlik, sablon, eslesmeli):
    for ad, deger in _ortam().items():
        desen = _satir_argumanlari(ad, deger)["regexp"]
        assert bool(re.search(desen, sablon.format(ad=ad))) is eslesmeli, (kimlik, desen)


# ================================================================================================
# T3 — GERÇEK Ansible modülü, tmp dosyada (ad-hoc, -c local; A1'e bağlantı YOK)
# ================================================================================================

_ILK_SATIR = 'PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"\n'


def _modul_kos(tmp_path: Path, dosya: Path, ad: str, deger: str, *bayraklar: str) -> tuple[bool, list[str], list[str]]:
    """Görevin ÇÖZÜLMÜŞ `lineinfile` argümanlarını (yol tmp'ye çevrilerek) ad-hoc koşar.
    Dönüş: (changed, fark eklenen satırlar, fark silinen satırlar) — fark yalnız `--diff` ile dolar.
    Çıktı `minimal` callback'inden okunur (`json` callback ansible-core'da YOK — ansible.posix'e ait)."""
    args = _satir_argumanlari(ad, deger)
    args["path"] = str(dosya)
    ahome = tmp_path / "ansible_home"
    ahome.mkdir(exist_ok=True)
    cfg = tmp_path / "bos.cfg"
    cfg.write_text("", encoding="utf-8")
    env = {**os.environ, "ANSIBLE_CONFIG": str(cfg), "ANSIBLE_HOME": str(ahome),
           "ANSIBLE_LOCAL_TEMP": str(ahome / "tmp"), "ANSIBLE_STDOUT_CALLBACK": "minimal",
           "ANSIBLE_NOCOLOR": "1", "ANSIBLE_DEPRECATION_WARNINGS": "0", "ANSIBLE_HOST_KEY_CHECKING": "0"}
    r = subprocess.run(
        [_ansible_ikili("ansible"), "localhost", "-i", "localhost,", "-c", "local",
         "-e", f"ansible_python_interpreter={sys.executable}",
         "-m", "ansible.builtin.lineinfile", "-a", json.dumps(args), *bayraklar],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"ansible rc {r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
    m = re.search(r"^localhost \| (CHANGED|SUCCESS) => (\{.*\})\s*$", r.stdout, re.M | re.S)
    assert m, f"ansible çıktısı çözümlenemedi:\n{r.stdout[-1500:]}"
    sonuc = json.loads(m.group(2))
    assert (m.group(1) == "CHANGED") is bool(sonuc.get("changed")), (m.group(1), sonuc)
    fark = r.stdout[:m.start()].splitlines()
    eklenen = [s[1:] for s in fark if s.startswith("+") and not s.startswith("+++")]
    silinen = [s[1:] for s in fark if s.startswith("-") and not s.startswith("---")]
    return bool(sonuc["changed"]), eklenen, silinen


def test_T3_GERCEK_modul_kuru_kosum_yalniz_iki_satir_EKLER_gercek_kosum_IDEMPOTENT(tmp_path):
    dosya = tmp_path / "environment"
    dosya.write_text(_ILK_SATIR, encoding="utf-8")
    dosya.chmod(0o640)                                   # varsayılan dışı mod: korunduğu ÖLÇÜLSÜN
    once = _sha(dosya)
    ortam = _ortam()
    # Kuru koşum (--check --diff): her öğe TEK satır ekler, hiçbir satır silmez, dosya DEĞİŞMEZ.
    for ad, deger in ortam.items():
        degisti, eklenen, silinen = _modul_kos(tmp_path, dosya, ad, deger, "--check", "--diff")
        assert degisti and eklenen == [f"{ad}={deger}"] and silinen == [], (ad, eklenen, silinen)
    assert _sha(dosya) == once, "kuru koşum dosyayı DEĞİŞTİRDİ"
    # Gerçek koşum: ilk satır yerinde, iki satır sonda, mod korunur.
    for ad, deger in ortam.items():
        assert _modul_kos(tmp_path, dosya, ad, deger)[0] is True
    satirlar = dosya.read_text(encoding="utf-8").splitlines(True)
    assert satirlar == [_ILK_SATIR, *(f"{ad}={deger}\n" for ad, deger in ortam.items())], satirlar
    assert (dosya.stat().st_mode & 0o777) == 0o640, oct(dosya.stat().st_mode)
    # İkinci koşum: değişiklik YOK (idempotent).
    for ad, deger in ortam.items():
        assert _modul_kos(tmp_path, dosya, ad, deger)[0] is False, f"{ad}: ikinci koşum 'changed'"


def test_T3b_GERCEK_modul_ayni_adin_eski_atamasi_TEKILLESIR(tmp_path):
    """Aynı ad elle 0'a çekilmişse ikinci satır EKLENMEZ, o satır düzeltilir (iki çelişik atama
    pam_env'de sıraya bağlı bir hükme dönerdi)."""
    ad, deger = next(iter(_ortam().items()))
    dosya = tmp_path / "environment"
    dosya.write_text(f"{_ILK_SATIR}export {ad}=0\n", encoding="utf-8")
    assert _modul_kos(tmp_path, dosya, ad, deger)[0] is True
    satirlar = dosya.read_text(encoding="utf-8").splitlines()
    assert satirlar == [_ILK_SATIR.rstrip("\n"), f"{ad}={deger}"], satirlar


# ================================================================================================
# T4 — BEDEL: A1'e giden yüzeyde ortamla ÇELİŞEN çağrı yok
# ================================================================================================

def _celisen(cagrilar) -> list[tuple[str, tuple[str, ...]]]:
    """`--locked` (ortamda rc 2) ya da `lock --check` (ortamda KÖR)."""
    return [(alt, sec) for alt, sec in cagrilar
            if any(s.split("=", 1)[0] == "--locked" for s in sec) or (alt == "lock" and "--check" in sec)]


def _a1_yuzeyi_cagrilari() -> dict[str, list[tuple[str, tuple[str, ...]]]]:
    d = _defaults()
    cikti: dict[str, list] = {}
    for p in sorted(GOREVLER.glob("*.yml")):                               # A0 rolü → A1
        cikti[p.name] = [c for cmd in _komutlar(yaml.safe_load(p.read_text(encoding="utf-8")))
                         for c in _uv_cagrilari(_sablon_coz(cmd, d))]
    a1_play = [pl for pl in _dagit_yml() if pl.get("hosts") != "localhost"]
    assert len(a1_play) == 1
    cikti["dagit.yml (A1 play)"] = [c for g in _play_gorevleri(a1_play[0]) if g.get("delegate_to") != "localhost"
                                    for c in _uv_cagrilari(_sablon_coz(_komut_metni(g), d))]
    for p in sorted((KOK / "deploy").rglob("*.sh")):                       # A1 betikleri (ssh gövdeleri dahil)
        parcalar, _ = _kabuk_parcalari(_UV_DEGISKEN.sub("uv", p.read_text(encoding="utf-8")))
        cikti[str(p.relative_to(KOK))] = [c for x in parcalar if x.tur != "yorum" for c in _uv_cagrilari(x.metin)]
    parcalar, _ = _md_parcalari(ELLE_RUNBOOK.read_text(encoding="utf-8"))  # elle A1 kılavuzu (kabuk çitleri)
    cikti[str(ELLE_RUNBOOK.relative_to(KOK))] = [c for x in parcalar if x.tur in ("kod", "tirnak")
                                                  for c in _uv_cagrilari(x.metin)]
    return cikti


def test_T4_BEDEL_A1_yuzeyinde_ortamla_CELISEN_uv_cagrisi_YOK():
    yuzey = _a1_yuzeyi_cagrilari()
    toplam = sum(len(v) for v in yuzey.values())
    assert toplam >= 20 and any(v for k, v in yuzey.items() if k.endswith(".yml")), f"A1 yüzeyi kör: {toplam}"
    celisen = {k: _celisen(v) for k, v in yuzey.items() if _celisen(v)}
    assert not celisen, (
        f"A1'e giden yüzeyde `UV_FROZEN=1` ile ÇELİŞEN çağrı: {celisen} — `--locked` orada rc 2 ile reddedilir, "
        "`uv lock --check` yalnız geçerlilik denetler (bayat kilitte rc 0 — KÖR kapı). Kilit tazeliği A1 "
        "DIŞINDA (dagit Play 1 / CI) ölçülür.")


@pytest.mark.parametrize("cagri, celisir", [
    ("uv run --locked python x", True), ("uv sync --locked=true", True), ("uv lock --check --offline", True),
    ("uv lock --check-exists", False), ("uv sync --frozen --no-dev", False), ("uv run --frozen --no-dev x", False),
])
def test_T4b_celiski_algilayici_POZITIF_KONTROL(cagri, celisir):
    assert bool(_celisen(_uv_cagrilari(cagri))) is celisir


def test_T4c_dagit_kilit_kapisi_A1_DISINDA_localhost_playinde():
    """Kilit tazeliği kapısı A1'de koşsaydı `/etc/environment` onu KÖRLEŞTİRİRDİ (Ansible ssh oturumu
    pam_env'den geçer). Kapı Play 1'de (hosts: localhost) yaşar."""
    yerler = [(pl.get("hosts"), g.get("delegate_to")) for pl in _dagit_yml() for g in _play_gorevleri(pl)
              if _celisen(_uv_cagrilari(_komut_metni(g)))]
    assert yerler and all(h == "localhost" or dt == "localhost" for h, dt in yerler), yerler


# ================================================================================================
# T5 — GERÇEK uv ile pozitif kontrol (depo kopyası, BOŞ önbellek, `--offline`; yazmaz)
# ================================================================================================

def _uv_kos(dizin: Path, onbellek: Path, argv: list[str], ortamli: bool) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("UV_")}
    env.update({"UV_CACHE_DIR": str(onbellek), "UV_PYTHON_DOWNLOADS": "never", "UV_NO_PROGRESS": "1"})
    if ortamli:
        env.update(_ortam())
    return subprocess.run([_uv_ikili(), *argv], cwd=dizin, env=env, capture_output=True, text=True, timeout=180)


def _kopya(tmp_path: Path, bayat: bool) -> Path:
    kopya = tmp_path / "proje"
    kopya.mkdir()
    for ad in ("pyproject.toml", "uv.lock"):
        (kopya / ad).write_bytes((KOK / ad).read_bytes())
    if bayat:   # kilitli sürümün HÂLÂ sağladığı gevşetme — v566 E4'ün ölçülmüş ayrışma durumu
        metin = (kopya / "pyproject.toml").read_text(encoding="utf-8")
        assert metin.count('"pandas>=2.1"') == 1, "ön koşul: dönüşüm hedefi pyproject'te tek değil"
        (kopya / "pyproject.toml").write_text(metin.replace('"pandas>=2.1"', '"pandas>=2.0"'), encoding="utf-8")
    return kopya


def _kurulacaklar(cikti: str) -> set[str]:
    return {re.sub(r"[-_.]+", "-", m.group(1)).lower() for m in re.finditer(r"^ \+ ([A-Za-z0-9][\w.-]*)==", cikti, re.M)}


def test_T5a_ortam_DEV_GRUBUNU_kurdurmaz(tmp_path):
    kopya = _kopya(tmp_path, bayat=False)
    veri = tomllib.loads((kopya / "pyproject.toml").read_text(encoding="utf-8"))
    dev = {re.sub(r"[-_.]+", "-", re.split(r"[<>=!~\[; ]", s, maxsplit=1)[0]).lower()
           for s in veri["dependency-groups"]["dev"] if isinstance(s, str)}
    ortamsiz = _uv_kos(kopya, tmp_path / "o1", ["sync", "--dry-run", "--offline"], ortamli=False)
    ortamli = _uv_kos(kopya, tmp_path / "o2", ["sync", "--dry-run", "--offline"], ortamli=True)
    assert ortamsiz.returncode == 0 and ortamli.returncode == 0, (ortamsiz.stderr[-600:], ortamli.stderr[-600:])
    k0, k1 = _kurulacaklar(ortamsiz.stdout + ortamsiz.stderr), _kurulacaklar(ortamli.stdout + ortamli.stderr)
    assert dev and dev <= k0, f"pozitif kontrol: ortamsız kurulum dev grubunu ({sorted(dev)}) içermeli: {sorted(k0)[:10]}"
    assert not (dev & k1) and k1 < k0, f"ortam altında dev grubu kuruluyor: {sorted(dev & k1)}"


def test_T5b_ortam_BAYAT_kilidi_COZMEZ_ve_YAZMAZ(tmp_path):
    kopya = _kopya(tmp_path, bayat=True)
    once = _sha(kopya / "uv.lock")
    ortamsiz = _uv_kos(kopya, tmp_path / "o1", ["sync", "--dry-run", "--offline"], ortamli=False)
    ortamli = _uv_kos(kopya, tmp_path / "o2", ["sync", "--dry-run", "--offline"], ortamli=True)
    assert ortamsiz.returncode != 0, "pozitif kontrol: bayat kopyada ortamsız eşitleme yeniden çözmeye kalkmalı"
    assert ortamli.returncode == 0, f"ortam altında kilit olduğu gibi kurulmalı:\n{ortamli.stderr[-800:]}"
    assert _sha(kopya / "uv.lock") == once


def test_T5c_BEDEL_olcumu_ortam_altinda_lock_check_KORLESIR_locked_REDDEDILIR(tmp_path):
    """Bedel bir İDDİA değil ölçüm: bu uv davranışı değişirse (ör. `--check` ortamı ezerse) başlıktaki
    BEDEL notu ve T4'ün gerekçesi bayatlar — bu çivi o gün öter."""
    kopya = _kopya(tmp_path, bayat=True)
    ortamsiz = _uv_kos(kopya, tmp_path / "o1", ["lock", "--check", "--offline"], ortamli=False)
    ortamli = _uv_kos(kopya, tmp_path / "o2", ["lock", "--check", "--offline"], ortamli=True)
    assert ortamsiz.returncode == 1, f"pozitif kontrol: bayat kilit ortamsız rc 1: {ortamsiz.returncode}"
    assert ortamli.returncode == 0 and "only checked for validity" in ortamli.stderr, (ortamli.returncode, ortamli.stderr)
    kilitli = _uv_kos(kopya, tmp_path / "o3", ["run", "--locked", "--offline", "true"], ortamli=True)
    assert kilitli.returncode == 2 and "cannot be used with" in kilitli.stderr, (kilitli.returncode, kilitli.stderr)

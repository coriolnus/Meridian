"""test_vault_db_kasa_v538.py — TSK-064: `sir_rotasyon.sh --db --vault` — Hindsight DB parolası KASADAN döner
(2026-09-24).

TASARIM (bağlayıcı): `docs/TASARIM-SIR-DB-KASA-2026-09-21.md` — §3 akış 1–9, §4 envanter, §5 riskler,
§6 çiviler. SIRA (B, değişmez): kasa → render kanıtı → ALTER ROLE → restart → kanıt. Parola İKİ
hakikat noktasında yaşar (Postgres rolü · kasadaki TAM DSN → Agent render'ı → hindsight-api) ve ikisi
aynı anda değişemez; geri ALINAMAYAN adım (ALTER) restart'ın hemen önündedir, ondan önceki her adım
KV v2 sürümüyle geri alınır.

DÜZENEK — ŞİMLER YENİDEN YAZILMADI. v447'nin sahte kökü ve PATH şimleri (`_sahte_ortam`: sudo · psql ·
systemctl · curl · install · id · rm · cp · stat) ile v521'in kasa ortamı (`_kasa_ortami`: jeton,
envanter, render tavanı) AYNEN kullanılır. Bu dosya üstlerine YALNIZ şunları ekler:
  · `vault` — KV v2 SÜRÜM MODELİ (v521'in şimi yalnız `kv put` tanır; bu akış `kv get` ·
    `kv metadata get` · `kv rollback` ister). Kasa tohumu ÜÇ sürüm taşır: geri alma YANLIŞ sürüme
    dönerse (ör. "bir önceki") kasadaki değer ölçülür ve ayrışır. Agent render'ı her yazımda
    (`SAHTE_RENDER=hep`) ya da hiç (`yok`) olur.
  · `psql` SARMALAYICISI — ALTER anında render hedefindeki DSN parolasını ALTER'ın parolasıyla
    kıyaslar ve OLAY yazar (B sırasının değişmezi: ALTER koşarken dosya ZATEN yeni parolayı taşır),
    sonra v447 şimine devreder. `SAHTE_ALTER_DUSER=1` ALTER'ı düşürür, `SAHTE_ALTER_ETKISIZ=1`
    kabul edip uygulamaz (kanıtın düştüğü dünya).
  · `systemctl` / `cmp` SARMALAYICILARI — restart'ı ve render kanıtı anını OLAY'a yazar, gerçeğe
    devreder.
Bütün sarmalayıcılar v447'nin `argv.log`una `OLAY …` satırı yazar: şimlerin kendi satırlarıyla
AYNI dosya → TEK zaman ekseni (Ç2'nin sıra iddiası buradan okunur).

BÖLÜMLER (tasarım §6 çivileri, numara aynen)
  Ç0  ithal edilen yollar bu ağacın (worktree tuzağı)
  Ç1  kuru plan 1–8 SIRAYLA, ADIYLA; hiçbir yazım/kasa çağrısı yok
  Ç2  gerçek akış sırası (kv put → render → ALTER → restart) ve ALTER render kanıtından ÖNCE koşamaz
  Ç3  render tavanı aşılınca ALTER YOK + kasa geri alınır
  Ç4  ALTER düşünce kasa geri alınır + render beklenir + die; "başarılı" satırı YOK
      (4b rollback düşerse YEDEK YOL `kv put` · 4c ikisi de düşerse BAĞIRIR)
  Ç5  parola / DSN hiçbir çıktıya, argv'ye, günlüğe DÜŞMEZ (hash de)
  Ç6  envanter bağı (`rotasyon_siri: HINDSIGHT_DB_PAROLA`) + v447/v485/v491/v521 hizası
  Ç7  eski `--db` yolu DEĞİŞMEDİ — bu dilimden ÖNCEKİ betikte ÖLÇÜLEN altın iz
  Ç8  ön kapılar (boş · SQL alfabesi · aynı parola) kasaya dokunmadan durur; kanıt düşerse
      kasa yolunun geri alma reçetesi basılır (dosya kopyası reçetesi DEĞİL)
  M   MUTASYONLAR — M0 çapalar tekil · M1–M5 brief'in beş mutasyonu · M6 yedek yol. Mutant betik
      tmp'ye yazılır (`_mutant`); özgün betik DEĞİŞMEZ.

SIR DEĞERİ YOK: her değer `SAHTE-` önekli ve sahtedir (v447 tohumları).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import stat

import pytest
import yaml

from tests import test_rotasyon_operator_mesajlari_v522 as v522
from tests import test_vault_dalga1_baglama_v521 as v521
from tests import test_vault_dalga2_v491 as v491
from tests import test_vault_faz2_v485 as v485
from tests.test_sir_rotasyon_v447 import (
    BETIK,
    DSN,
    ENVANTER,
    ESKI,
    _betik_kopyalari,
    _envanter_kopyalari,
    _kos,
    _mutant,
)

DB_SIR = "HINDSIGHT_DB_PAROLA"
DB_KV = "HINDSIGHT_API_DATABASE_URL"
DB_KASA = "secret/meridian/HINDSIGHT_API_DATABASE_URL"
DB_HEDEF = "/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL"
BIRIM = "hindsight-api.service"

#: Yeni parola SQL literal alfabesinde (`[A-Za-z0-9_-]`, yardımcının `sql-uret` kapısı).
YENI_PG = "SAHTE-YENI-PG-0538"
#: Kasanın ESKİ sürümleri — güncel (v3) v447'nin DSN'idir (render hedefi tohumuyla EŞİT, canlının hâli).
ONCEKI_PG = ("SAHTE-ONCEKI-PG-V1", "SAHTE-ONCEKI-PG-V2")


def _dsn(parola: str) -> str:
    """v447 DSN'inin YALNIZ parola alanı değişmiş hâli (query korunur — `yaz-url` sözleşmesi)."""
    assert DSN.count(ESKI["pg"]) == 1, DSN
    return DSN.replace(ESKI["pg"], parola)


YENI_DSN = _dsn(YENI_PG)
KASA_TOHUM = [_dsn(ONCEKI_PG[0]), _dsn(ONCEKI_PG[1]), DSN]
ESKI_SURUM = len(KASA_TOHUM)          # put ÖNCESİ current_version → geri alma hedefi

#: Hiçbir çıktıya/günlüğe düşmeyecek değerler — parolalar, TAM DSN'ler ve yönetici jetonu.
SIRLAR = (YENI_PG, ESKI["pg"], *ONCEKI_PG, YENI_DSN, *KASA_TOHUM, "SAHTE-hvs-yonetici")

UYARI = "VAULT AGENT RENDER HEDEFİ"
ALTER_DUSTU_METNI = "ALTER ROLE başarısız — parola DEĞİŞMEDİ, kasa geri alındı"


# =================================================================================================
# ŞİMLER — bu dosyanın EKLERİ (v447/v521 şimleri aynen altta koşar)
# =================================================================================================
SIM_KASA_DB = '''#!/usr/bin/env python3
"""KV v2 sürüm modeli + sahte Agent. Değer YALNIZ stdin'den gelir, argv'ye girmez; OLAY satırı değer taşımaz."""
import json, os, sys
DURUM = __DURUM__
ESLEME = __ESLEME__
KOK = __KOK__
OLAY = os.path.join(KOK, ".sahte", "argv.log")
a = sys.argv[1:]
with open(__LOG__, "a", encoding="utf-8") as fh:
    fh.write(" ".join(a) + "\\n")


def olay(s):
    with open(OLAY, "a", encoding="utf-8") as fh:
        fh.write("OLAY " + s + "\\n")


def oku():
    with open(DURUM, encoding="utf-8") as fh:
        return json.load(fh)


def yaz(d):
    with open(DURUM, "w", encoding="utf-8") as fh:
        json.dump(d, fh)


def render(yol, d):
    if os.environ.get("SAHTE_RENDER", "hep") != "hep" or yol not in ESLEME:
        return
    with open(KOK + ESLEME[yol], "w", encoding="utf-8") as fh:
        fh.write(d[yol][-1])
    olay("render %s v%d" % (yol, len(d[yol])))


def sayac_izin():
    """SAHTE_PUT_IZIN=<n>: ilk n yazım geçer, sonrakiler düşer (geri almanın YEDEK yolunu düşürmek için)."""
    izin = os.environ.get("SAHTE_PUT_IZIN")
    if izin is None:
        return True
    yol = os.path.join(KOK, ".sahte", "kasa_put_sayac")
    n = int(open(yol).read()) if os.path.exists(yol) else 0
    with open(yol, "w") as fh:
        fh.write(str(n + 1))
    return n < int(izin)


if a[:1] == ["login"]:
    sys.stdin.read()
    sys.exit(0)
if a[:2] == ["kv", "get"]:
    yol, d = a[-1], oku()
    if "-field=value" not in a:
        sys.stderr.write("sim vault: yalnız -field=value\\n"); sys.exit(2)
    if yol not in d:
        sys.stderr.write("No value found at %s\\n" % yol); sys.exit(2)
    olay("kv-get " + yol)
    sys.stdout.write(d[yol][-1])
    sys.exit(0)
if a[:3] == ["kv", "metadata", "get"]:
    yol, d = a[-1], oku()
    if "-format=json" not in a:
        sys.stderr.write("sim vault: yalnız -format=json\\n"); sys.exit(2)
    n = len(d.get(yol, []))
    olay("kv-metadata " + yol)
    print(json.dumps({"data": {"current_version": n,
                               "versions": {str(i + 1): {"destroyed": False} for i in range(n)}}}))
    sys.exit(0)
if a[:2] == ["kv", "put"] and a[3:] == ["value=-"]:
    yol, deger = a[2], sys.stdin.read()
    if not sayac_izin():
        olay("kv-put-DUSTU " + yol)
        sys.stderr.write("Error writing data to %s: permission denied\\n" % yol); sys.exit(2)
    d = oku()
    d.setdefault(yol, []).append(deger)
    yaz(d)
    olay("kv-put %s v%d" % (yol, len(d[yol])))
    render(yol, d)
    sys.exit(0)
if a[:2] == ["kv", "rollback"]:
    yol = a[-1]
    surum = int(next(x.split("=", 1)[1] for x in a if x.startswith("-version=")))
    if os.environ.get("SAHTE_ROLLBACK_KIRIK") == "1":
        olay("kv-rollback-DUSTU %s -version=%d" % (yol, surum))
        sys.stderr.write("Error: permission denied\\n"); sys.exit(2)
    d = oku()
    d[yol].append(d[yol][surum - 1])
    yaz(d)
    olay("kv-rollback %s -version=%d v%d" % (yol, surum, len(d[yol])))
    render(yol, d)
    sys.exit(0)
sys.stderr.write("sim vault: tanınmayan çağrı: %s\\n" % a)
sys.exit(2)
'''

SIM_PSQL_SARMA = '''#!/usr/bin/env python3
"""ALTER anında render hedefi parolası == ALTER parolası mı (B sırasının değişmezi) → OLAY; sonra v447 şimi."""
import os, re, subprocess, sys
from urllib.parse import unquote, urlsplit
ASIL = __ASIL__
KOK = os.environ["SIR_ROT_KOK"]
a = sys.argv[1:]


def olay(s):
    with open(os.path.join(KOK, ".sahte", "argv.log"), "a", encoding="utf-8") as fh:
        fh.write("OLAY " + s + "\\n")


if "-f" in a and a[a.index("-f") + 1] == "-":
    sql = sys.stdin.read()
    m = re.search(r"ALTER ROLE (\\w+) PASSWORD '([^']+)'", sql)
    try:
        with open(KOK + __HEDEF__, encoding="utf-8") as fh:
            dosya = unquote(urlsplit(fh.read().strip()).password or "")
    except OSError:
        dosya = None
    durum = "ESIT" if m and dosya == m.group(2) else "AYRI"
    if os.environ.get("SAHTE_ALTER_DUSER") == "1":
        olay("alter-DUSTU render=" + durum)
        sys.stderr.write("psql: ERROR:  permission denied to alter role\\n"); sys.exit(3)
    olay("alter render=" + durum)
    if os.environ.get("SAHTE_ALTER_ETKISIZ") == "1":
        sys.exit(0)
    sys.exit(subprocess.run([ASIL] + a, input=sql, text=True).returncode)
os.execv(ASIL, [ASIL] + a)
'''

SIM_SYSTEMCTL_SARMA = '''#!/usr/bin/env python3
import os, sys
a = sys.argv[1:]
if len(a) >= 2 and a[0] == "restart":
    with open(os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "argv.log"), "a", encoding="utf-8") as fh:
        fh.write("OLAY restart " + a[1] + "\\n")
os.execv(__ASIL__, [__ASIL__] + a)
'''

SIM_CMP_SARMA = '''#!/usr/bin/env python3
import os, subprocess, sys
a = sys.argv[1:]
r = subprocess.run([__ASIL__] + a)
adlar = " ".join(os.path.basename(x) for x in a if not x.startswith("-"))
with open(os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "argv.log"), "a", encoding="utf-8") as fh:
    fh.write("OLAY cmp %s %s\\n" % ("ESIT" if r.returncode == 0 else "AYRI", adlar))
sys.exit(r.returncode)
'''

_BAYRAKLAR = ("SAHTE_RENDER", "SAHTE_ALTER_DUSER", "SAHTE_ALTER_ETKISIZ", "SAHTE_ROLLBACK_KIRIK",
              "SAHTE_PUT_IZIN")


def _db_ortami(tmp_path: pathlib.Path, envanter: pathlib.Path = ENVANTER,
               **bayrak: str) -> tuple[pathlib.Path, dict, pathlib.Path, pathlib.Path]:
    """v521 kasa ortamı (v447 sahte kök + jeton + envanter + render tavanı) + bu dosyanın ekleri."""
    kok, ortam, _ = v521._kasa_ortami(tmp_path, envanter=envanter)
    esleme = {g["vault_yolu"]: g["hedef"]
              for g in yaml.safe_load(envanter.read_text(encoding="utf-8"))["vault_kv"] if "hedef" in g}
    durum = tmp_path / "kasa_v538.json"
    durum.write_text(json.dumps({DB_KASA: KASA_TOHUM}), encoding="utf-8")
    log = tmp_path / "kasa_v538_argv.log"
    binn = tmp_path / "bin_v538"
    binn.mkdir()
    asil = tmp_path / "bin"          # v447 şimleri
    cmp_asil = shutil.which("cmp")
    assert cmp_asil, "gerçek cmp bulunamadı"
    govdeler = {
        "vault": SIM_KASA_DB.replace("__DURUM__", repr(str(durum))).replace("__ESLEME__", repr(esleme))
                            .replace("__KOK__", repr(str(kok))).replace("__LOG__", repr(str(log))),
        "psql": SIM_PSQL_SARMA.replace("__ASIL__", repr(str(asil / "psql")))
                              .replace("__HEDEF__", repr(DB_HEDEF)),
        "systemctl": SIM_SYSTEMCTL_SARMA.replace("__ASIL__", repr(str(asil / "systemctl"))),
        "cmp": SIM_CMP_SARMA.replace("__ASIL__", repr(cmp_asil)),
    }
    for ad, govde in govdeler.items():
        (binn / ad).write_text(govde, encoding="utf-8")
        (binn / ad).chmod(0o755)
    ortam = dict(ortam, PATH=f"{binn}:{ortam['PATH']}", VAULT_BIN=str(binn / "vault"))
    for b in _BAYRAKLAR:
        ortam.pop(b, None)
    ortam.update(bayrak)
    return kok, ortam, log, durum


def _olaylar(kok: pathlib.Path) -> list[str]:
    return [s[len("OLAY "):] for s in (kok / ".sahte/argv.log").read_text(encoding="utf-8").splitlines()
            if s.startswith("OLAY ")]


def _kasa(durum: pathlib.Path) -> list[str]:
    return json.loads(durum.read_text(encoding="utf-8"))[DB_KASA]


def _pg(kok: pathlib.Path) -> str:
    return (kok / ".sahte/pg_parola").read_text(encoding="utf-8").strip()


def _render(kok: pathlib.Path) -> str:
    return (kok / DB_HEDEF.lstrip("/")).read_text(encoding="utf-8").strip()


def _restartlar(kok: pathlib.Path) -> list[str]:
    return (kok / ".sahte/systemctl.log").read_text(encoding="utf-8").split()


def _ilk(olaylar: list[str], onek: str, bas: int = 0) -> int:
    for i in range(bas, len(olaylar)):
        if olaylar[i].startswith(onek):
            return i
    raise AssertionError(f"olay yok: {onek!r} (≥{bas})\n" + "\n".join(olaylar))


def _sir_yok(r, kok: pathlib.Path, *loglar: pathlib.Path) -> None:
    """Ç5 sözleşmesi: değer ve değerin sha256'sı (tam ya da ilk 8 hane) hiçbir yüzeyde yok."""
    yuzeyler = {"stdout": r.stdout, "stderr": r.stderr,
                "argv.log": (kok / ".sahte/argv.log").read_text(encoding="utf-8")}
    for log in loglar:
        if log.exists():
            yuzeyler[log.name] = log.read_text(encoding="utf-8")
    for etiket, metin in yuzeyler.items():
        for d in SIRLAR:
            assert d not in metin, f"SIR DEĞERİ {etiket} içine düştü: {d}"
            h = hashlib.sha256(d.encode()).hexdigest()
            assert h[:8] not in metin, f"değerin HASH'i {etiket} içine düştü: {d}"


# =================================================================================================
# Ç1 — KURU PLAN
# =================================================================================================

def test_C0_ITHAL_edilen_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v521 A0 ile aynı): ithal edilen modül başka ağaçtan yüklenirse bütün çiviler
    BAŞKA bir betiği ölçer — sessizce."""
    kok = pathlib.Path(__file__).resolve().parents[1]
    for yol in (BETIK, ENVANTER, *(pathlib.Path(m.__file__) for m in (v485, v491, v521, v522))):
        assert yol.resolve().is_relative_to(kok), f"yabancı ağaçtan ithal: {yol}"


def _plan_satirlari(cikti: str) -> dict[int, str]:
    bulunan = re.findall(r"^  ([1-9])\. (.*)$", cikti, re.M)
    sayilar = [int(n) for n, _ in bulunan]
    assert sayilar == list(range(1, 9)), f"plan 1–8 SIRAYLA ve TEKER kez değil: {sayilar}\n{cikti}"
    return {int(n): s for n, s in bulunan}


def test_C1_KURU_plan_1_8_SIRAYLA_ADIYLA_hicbir_yazim_ve_kasa_cagrisi_YOK(tmp_path):
    kok, ortam, log, durum = _db_ortami(tmp_path)
    once = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    r = _kos(BETIK, ortam, "--db", "--vault", "--kuru")
    assert r.returncode == 0, f"kuru koşum düştü:\n{r.stdout}\n{r.stderr}"
    plan = _plan_satirlari(r.stdout)
    assert "KASADAN" in plan[1] and DB_KASA in plan[1], plan[1]
    assert "operatör" in plan[2] and DB_SIR in plan[2], plan[2]
    assert "YALNIZ parola" in plan[3], plan[3]
    assert DB_KASA in plan[4] and "current_version" in plan[4] and "rollback" in plan[4], plan[4]
    assert DB_HEDEF in plan[5] and "ALTER ROLE KOŞMAZ" in plan[5], plan[5]
    assert plan[6].startswith("ALTER ROLE hindsight PASSWORD"), plan[6]
    assert set(re.findall(r"[a-z0-9-]+\.service", plan[7])) == {BIRIM}, plan[7]
    assert "FATAL" in plan[8] and "select 1" in plan[8], plan[8]
    # Tasarım §3.9: kasa yolu Agent'ı ZATEN besler — eski yolun uyarısı burada GEREKMEZ.
    assert UYARI not in r.stdout + r.stderr and "kasa yolunu kullanın" not in r.stdout, r.stdout
    assert len([s for s in r.stdout.splitlines() if "DEĞER KAYNAĞI" in s]) == 1, r.stdout
    # Hiçbir yazım: dosya ağacı (v447 argv günlüğü hariç) AYNI, kasa/psql/restart/cmp olayı YOK.
    sonra = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    degisen = {str(p.relative_to(tmp_path)) for p in set(once) | set(sonra) if once.get(p) != sonra.get(p)}
    assert degisen <= {"kok/.sahte/argv.log"}, degisen
    assert not _olaylar(kok), _olaylar(kok)
    assert not log.exists(), f"kuru koşum kasaya çağrı yaptı:\n{log.read_text()}"
    assert _kasa(durum) == KASA_TOHUM and _pg(kok) == ESKI["pg"] and not _restartlar(kok)


# =================================================================================================
# Ç2 — GERÇEK AKIŞ SIRASI
# =================================================================================================

def test_C2_GERCEK_akis_kv_put_RENDER_ALTER_restart_SIRASI_ve_ALTER_render_kanitindan_ONCE_KOSAMAZ(tmp_path):
    kok, ortam, log, durum = _db_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    o = _olaylar(kok)
    put = _ilk(o, f"kv-put {DB_KASA} v{ESKI_SURUM + 1}")
    render = _ilk(o, f"render {DB_KASA} v{ESKI_SURUM + 1}", put)
    # Betiğin render KANITI: yeni DSN ↔ render hedefinin kanonik kopyası BİREBİR (`_render_bekle`).
    kanit = _ilk(o, "cmp ESIT db_yeni_dsn vault_render_kanon", render)
    alter = _ilk(o, "alter ", kanit)
    restart = _ilk(o, f"restart {BIRIM}", alter)
    assert put < render < kanit < alter < restart, o
    assert o[alter] == "alter render=ESIT", f"ALTER koşarken render hedefi yeni parolayı TAŞIMIYORDU: {o[alter]}"
    assert [x for x in o if x.startswith(("kv-put", "alter", "kv-rollback"))] == [
        f"kv-put {DB_KASA} v{ESKI_SURUM + 1}", "alter render=ESIT"], o
    # Durum: kasa · dosya · rol · birim — dördü de YENİ, kanıt ikili.
    assert _kasa(durum)[-1] == YENI_DSN and len(_kasa(durum)) == ESKI_SURUM + 1
    assert _render(kok) == YENI_DSN and _pg(kok) == YENI_PG
    assert _restartlar(kok) == [BIRIM], _restartlar(kok)
    assert "yeni parola: select 1 → 1" in r.stdout and "eski parola: FATAL" in r.stdout, r.stdout
    assert re.search(r"pencere B \(render kanıtı → ALTER ROLE\): \d+ s", r.stdout), r.stdout
    # Eski DSN KASADAN yedeğe 0600 (tasarım §3.3) — geri almanın girdisi.
    yedekler = sorted((kok / "root").glob("sir-yedek-*-db"))
    assert len(yedekler) == 1, yedekler
    eski = yedekler[0] / "vault" / DB_KASA
    assert eski.read_text(encoding="utf-8").strip() == DSN
    assert stat.S_IMODE(eski.stat().st_mode) == 0o600, oct(eski.stat().st_mode)
    # Eski yolun uyarısı ve url kopyasının ELLE yazımı YOK (url kopyası Agent'ındır).
    assert UYARI not in r.stdout + r.stderr, r.stdout
    assert f"yazıldı: {DB_HEDEF}" not in r.stdout, "kasa yolu render hedefine ELLE yazdı"
    _sir_yok(r, kok, log)


# =================================================================================================
# Ç3 — RENDER TAVANI
# =================================================================================================

def test_C3_RENDER_TAVANI_asilinca_ALTER_YOK_kasa_GERI_ALINIR_OLCULEMEDI(tmp_path):
    kok, ortam, log, durum = _db_ortami(tmp_path, SAHTE_RENDER="yok")
    r = _kos(BETIK, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    assert r.returncode == 2, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    o = _olaylar(kok)
    assert not [x for x in o if x.startswith("alter")], f"render kanıtı YOKKEN ALTER koştu: {o}"
    _ilk(o, f"kv-rollback {DB_KASA} -version={ESKI_SURUM}", _ilk(o, "kv-put"))
    assert _kasa(durum)[-1] == DSN, "kasa ESKİ DSN'e dönmedi"
    assert _pg(kok) == ESKI["pg"] and not _restartlar(kok)
    assert "ÖLÇÜLEMEDİ" in r.stderr and "ALTER ROLE KOŞMADI" in r.stderr, r.stderr
    assert "kasa ESKİ DSN'e geri alındı" in r.stdout + r.stderr, r.stdout + r.stderr
    _sir_yok(r, kok, log)


# =================================================================================================
# Ç4 — ALTER DÜŞER
# =================================================================================================

def _basari_satiri_yok(r) -> None:
    tum = r.stdout + r.stderr
    assert "başarılı" not in tum, tum
    assert "ALTER ROLE hindsight uygulandı" not in tum and "select 1 → 1" not in tum, tum


def test_C4_ALTER_duserse_kasa_GERI_ALINIR_render_BEKLENIR_DIE_basarili_satiri_YOK(tmp_path):
    kok, ortam, log, durum = _db_ortami(tmp_path, SAHTE_ALTER_DUSER="1")
    r = _kos(BETIK, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert ALTER_DUSTU_METNI in r.stderr, r.stderr
    o = _olaylar(kok)
    alter = _ilk(o, "alter-DUSTU")
    geri = _ilk(o, f"kv-rollback {DB_KASA} -version={ESKI_SURUM}", alter)
    donus = _ilk(o, f"render {DB_KASA} v{ESKI_SURUM + 2}", geri)
    _ilk(o, "cmp ESIT db_eski_dsn vault_render_kanon", donus)   # ESKİ DSN'in render'ı ÖLÇÜLDÜ
    assert f"render ESKİ DSN'e döndü: {DB_HEDEF}" in r.stdout, r.stdout
    assert _kasa(durum)[-1] == DSN and _render(kok) == DSN
    assert _pg(kok) == ESKI["pg"] and not _restartlar(kok)
    _basari_satiri_yok(r)
    _sir_yok(r, kok, log)


def test_C4b_ROLLBACK_duserse_YEDEK_YOL_eski_DSN_kv_put_ile_geri_yazilir(tmp_path):
    kok, ortam, log, durum = _db_ortami(tmp_path, SAHTE_ALTER_DUSER="1", SAHTE_ROLLBACK_KIRIK="1")
    r = _kos(BETIK, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert ALTER_DUSTU_METNI in r.stderr, r.stderr
    o = _olaylar(kok)
    dustu = _ilk(o, f"kv-rollback-DUSTU {DB_KASA} -version={ESKI_SURUM}")
    _ilk(o, f"kv-put {DB_KASA} v{ESKI_SURUM + 2}", dustu)
    assert "rollback DÜŞTÜ" in r.stderr, r.stderr
    assert _kasa(durum)[-1] == DSN and _render(kok) == DSN and _pg(kok) == ESKI["pg"]
    _basari_satiri_yok(r)
    _sir_yok(r, kok, log)


def test_C4c_IKI_geri_alma_yolu_da_duserse_BAGIRIR_ve_KASA_RECETESI(tmp_path):
    """Kasa YENİ, DB ESKİ: hindsight-api bir sonraki restart'ta düşer. Sessiz kalamaz."""
    kok, ortam, log, durum = _db_ortami(tmp_path, SAHTE_ALTER_DUSER="1", SAHTE_ROLLBACK_KIRIK="1",
                                        SAHTE_PUT_IZIN="1")
    r = _kos(BETIK, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "KASA GERİ ALINAMADI" in r.stderr, r.stderr
    assert ALTER_DUSTU_METNI not in r.stderr, "geri alınamayan kasa 'geri alındı' diye raporlandı"
    assert f"vault kv rollback -version={ESKI_SURUM} {DB_KASA}" in r.stderr, r.stderr
    assert _kasa(durum)[-1] == YENI_DSN and _pg(kok) == ESKI["pg"] and not _restartlar(kok)
    _basari_satiri_yok(r)
    _sir_yok(r, kok, log)


# =================================================================================================
# Ç5 — DEĞER HİÇBİR YÜZEYE DÜŞMEZ
# =================================================================================================

@pytest.mark.parametrize("etiket,bayrak,args,girdi", [
    ("basari", {}, ("--db", "--vault"), f"{YENI_PG}\n"),
    ("render_yok", {"SAHTE_RENDER": "yok"}, ("--db", "--vault"), f"{YENI_PG}\n"),
    ("alter_duser", {"SAHTE_ALTER_DUSER": "1"}, ("--db", "--vault"), f"{YENI_PG}\n"),
    ("kanit_duser", {"SAHTE_ALTER_ETKISIZ": "1"}, ("--db", "--vault"), f"{YENI_PG}\n"),
    ("kuru", {}, ("--db", "--vault", "--kuru"), ""),
], ids=["basari", "render_yok", "alter_duser", "kanit_duser", "kuru"])
def test_C5_PAROLA_ve_DSN_hicbir_ciktiya_ARGVye_gunluge_DUSMEZ(tmp_path, etiket, bayrak, args, girdi):
    kok, ortam, log, _ = _db_ortami(tmp_path, **bayrak)
    r = _kos(BETIK, ortam, *args, girdi=girdi)
    assert r.returncode in (0, 1, 2), f"{etiket}: {r.returncode}\n{r.stdout}\n{r.stderr}"
    _sir_yok(r, kok, log)
    # Değer argv'ye de girmez: kasaya STDIN'den, rolün parolası SQL dosyasından (`psql -f -`).
    assert etiket == "kuru" or "kv put secret/meridian/HINDSIGHT_API_DATABASE_URL value=-" in log.read_text(
        encoding="utf-8"), log.read_text(encoding="utf-8")


# =================================================================================================
# Ç6 — ENVANTER BAĞI
# =================================================================================================

def _c6_denetle(envanter: pathlib.Path, tmp_path: pathlib.Path) -> None:
    kv = {g["ad"]: g for g in yaml.safe_load(envanter.read_text(encoding="utf-8"))["vault_kv"]}
    g = kv[DB_KV]
    assert g.get("rotasyon_siri") == DB_SIR, f"{DB_KV}: rotasyon_siri {g.get('rotasyon_siri')!r}"
    assert [a for a, x in kv.items() if x.get("rotasyon_siri") == DB_SIR] == [DB_KV]
    # Dalga-1 girdisi: YALNIZ `rotasyon_siri` eklenir (v485 E1 dar gevşemesi) — kaynak/kopya YOK.
    assert set(g) == {"ad", "vault_yolu", "hedef", "mod", "sahip", "tuketici", "rotasyon_siri"}, sorted(g)
    assert (g["vault_yolu"], g["hedef"]) == (DB_KASA, DB_HEDEF), g
    # `--db`nin iki kopyası AYNEN ve AYNI SIRADA (sql → url): kasa yolu url'yi Agent'a bırakır, sql'i koşar.
    betik = [(k["tur"], k["yol"]) for k in _betik_kopyalari() if k["sir"] == DB_SIR]
    assert betik == [("sql", "hindsight"), ("url", DB_HEDEF)], betik
    env = [(k["tur"], k["yol"]) for k in _envanter_kopyalari() if k["sir"] == DB_SIR]
    assert env == betik, (env, betik)
    # Bağ davranışa İNER: aynı envanterle kasa yolunun kuru planı DB kasa yolunu gösterir.
    kod = v521._kv_satirlari(envanter, DB_SIR)
    assert kod.returncode == 0 and kod.stdout.splitlines() == [
        f"{DB_KV}\t{DB_KASA}\t{DB_HEDEF}\t{DB_SIR}\t-"], (kod.stdout, kod.stderr)
    _, ortam, _, _ = _db_ortami(tmp_path, envanter=envanter)
    r = _kos(BETIK, ortam, "--db", "--vault", "--kuru")
    assert r.returncode == 0 and DB_KASA in _plan_satirlari(r.stdout)[4], f"{r.stdout}\n{r.stderr}"


def test_C6_ENVANTER_BAGI_ve_KOMSU_civiler(tmp_path):
    _c6_denetle(ENVANTER, tmp_path)
    # Komşu çiviler aynı bağı ölçer (pozitif kontrol — gerçek envanterde YEŞİL).
    v485.test_E1_vault_kv_DALGA1_kumesini_tam_tasir()
    v491.test_A5_ROTASYON_SIRI_bagi_kopya_kumesiyle_BIREBIR()
    v521.test_A2_DB_URL_BAGLANDI_ve_YALNIZ_o_girdi_DB_parolasini_gosterir()
    v521.test_A3_BAGLI_KUME_tablonun_BUTUN_sirlari()


# =================================================================================================
# Ç7 — ESKİ `--db` YOLU DEĞİŞMEDİ (altın iz)
# =================================================================================================
# ALTIN İZ bu dilimden ÖNCEKİ betikte (ana dal 59aeff90) AYNI yardımcıyla pytest içinde ÖLÇÜLDÜ ve
# buraya yapıştırıldı — elle yazılmadı. Kıyas: çıkış kodu · şimlerin argv günlüğü (hangi komut, hangi
# sırayla, hangi argümanla) · restart günlüğü · dosya DURUMLARI · stdout (UYARI bloğu HARİÇ: bağ onun
# SINIFINI bağsızdan bağlıya çevirir — o metin v522 A1/A4'te ayrıca ölçülür). Normalleştirme yalnız
# koşuma özgü dizgeleri siler (tmp kökü, çalışma dizini adı, yedek damgası, saniye).

def _norm(metin: str, dizin: pathlib.Path) -> str:
    metin = metin.replace(str(dizin), "<T>").replace(str(BETIK), "<BETIK>")
    metin = re.sub(r"sir-rot\.[A-Za-z0-9]+", "sir-rot.X", metin)
    metin = re.sub(r"sir-yedek-\d{8}T\d{6}Z", "sir-yedek-TS", metin)
    return re.sub(r"\b\d+ s\b", "N s", metin)


def _uyarisiz(metin: str) -> list[str]:
    out, atla = [], False
    for s in metin.splitlines():
        if s.startswith("  !! UYARI — " + UYARI):
            atla = True
            continue
        if atla and s.startswith("     "):
            continue
        atla = False
        out.append(s)
    return out


def _db_izi(betik: pathlib.Path, dizin: pathlib.Path, *args: str) -> dict:
    dizin.mkdir()
    kok, ortam, _ = v521._kasa_ortami(dizin)
    ortam.pop("VAULT_POLITIKA_URETICI", None)
    agac = lambda: {p.relative_to(kok).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
                    for p in sorted(kok.rglob("*")) if p.is_file() and ".sahte" not in p.parts}
    once = agac()
    r = _kos(betik, ortam, *args)
    sonra = agac()
    dosyalar = {}
    for rel in sorted(set(once) | set(sonra)):
        durum = ("SİLİNDİ" if rel not in sonra else "YENİ" if rel not in once
                 else "AYNI" if once[rel] == sonra[rel] else "DEĞİŞTİ")
        if durum != "AYNI":
            dosyalar[_norm(rel, dizin)] = durum
    return {"rc": r.returncode,
            "argv": _norm((kok / ".sahte/argv.log").read_text(encoding="utf-8"), dizin).splitlines(),
            "systemctl": (kok / ".sahte/systemctl.log").read_text(encoding="utf-8").split(),
            "dosyalar": dosyalar,
            "stdout": _uyarisiz(_norm(r.stdout, dizin)),
            "stderr": _uyarisiz(_norm(r.stderr, dizin))}


ALTIN_DB_KURU: dict = {
    "rc": 0,
    "argv": [],
    "systemctl": [],
    "dosyalar": {},
    "stdout": [
        "=== ROTASYON: Postgres 'hindsight' rol parolası ===",
        "=== KURU KOŞUM: --db (HİÇBİR ŞEY YAZILMADI) ===",
        "  yazılacak: ALTER ROLE hindsight PASSWORD (SQL dosyası, koşumdan sonra silinir)",
        "  yazılacak: /etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL  (url, HINDSIGHT_DB_PAROLA)",
        "  yeniden başlatılacak: hindsight-api.service",
        "  sır → tüketici birimler (gerçek koşumda YALNIZ yazılan sırrınki yeniden başlar):",
        "    · HINDSIGHT_DB_PAROLA → hindsight-api.service",
        "  hazırlık beklemesi (her uç 0.N s aralıkla yoklanır; aşımda ÖLÇÜLEMEDİ).",
        "     BEDEL: bu alt komutta her birim 1 kez yeniden başlar ve her restart'ın ardından",
        "     hazırlık beklenir — satırdaki tavan BİR restart içindir, en kötü hâl 1 katıdır:",
        "    · hindsight-api → http://hafiza/health  kabul: HTTP 200  tavan: N s × 1 restart = en kötü N s",
        "  ÖN KOŞUL: sudo systemctl stop meridian-tick-watchdog.timer (sonda geri aç)",
        "  tavanı yükseltmek gerekirse (DÜZ sudo ortam değişkenini DÜŞÜRÜR):",
        "    sudo env HAZIR_TAVAN_S_hindsight_api=20 ./deploy/oracle-a1/sir_rotasyon.sh --db",
        "  yedek dizini: <T>/kok/root/sir-yedek-<UTC ts>-db"
    ],
    "stderr": []
}
ALTIN_DB_GERCEK: dict = {
    "rc": 0,
    "argv": [
        "sudo install -d -m 0700 -o root -g root <T>/kok/root/sir-yedek-TS-db",
        "install -d -m 0700 -o root -g root <T>/kok/root/sir-yedek-TS-db",
        "sudo test -e <T>/kok/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL",
        "sudo install -d -m 0700 -o root -g root <T>/kok/root/sir-yedek-TS-db/etc/hindsight/creds",
        "install -d -m 0700 -o root -g root <T>/kok/root/sir-yedek-TS-db/etc/hindsight/creds",
        "sudo cp -p <T>/kok/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL <T>/kok/root/sir-yedek-TS-db/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL",
        "sudo cp -p <T>/kok/root/sir-yedek-TS-db/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL <T>/sir-rot.X/eski_url",
        "sudo python3 <T>/sir-rot.X/yardimci.py sql-uret <T>/sir-rot.X/rol.sql hindsight <T>/sir-rot.X/yeni",
        "sudo -u postgres psql -v ON_ERROR_STOP=1 -q -f -",
        "psql -v ON_ERROR_STOP=1 -q -f -",
        "sudo rm -f <T>/sir-rot.X/rol.sql",
        "sudo test ! -e <T>/sir-rot.X/rol.sql",
        "sudo test -f <T>/kok/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL",
        "sudo python3 <T>/sir-rot.X/yardimci.py yaz-url <T>/kok/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL <T>/sir-rot.X/yeni koru koru",
        "sudo systemctl restart hindsight-api.service",
        "sudo test -e <T>/kok/run/credentials/hindsight-api.service/HINDSIGHT_API_DATABASE_URL",
        "sudo stat -c %s <T>/kok/run/credentials/hindsight-api.service/HINDSIGHT_API_DATABASE_URL",
        "sudo stat -f %z <T>/kok/run/credentials/hindsight-api.service/HINDSIGHT_API_DATABASE_URL",
        "sudo python3 <T>/sir-rot.X/yardimci.py kanit-cfg <T>/sir-rot.X/kanit.cfg http://hafiza/health - - - <T>/sir-rot.X/kanit.out -",
        "curl -K <T>/sir-rot.X/kanit.cfg",
        "sudo python3 <T>/sir-rot.X/yardimci.py dsn-uc <T>/kok/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL",
        "sudo python3 <T>/sir-rot.X/yardimci.py pgpass <T>/sir-rot.X/pgpass_yeni <T>/kok/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL",
        "psql -w -tAX -h 127.0.0.1 -p 5432 -U hindsight -d hindsight -c select 1",
        "sudo python3 <T>/sir-rot.X/yardimci.py pgpass <T>/sir-rot.X/pgpass_eski <T>/sir-rot.X/eski_url",
        "psql -w -tAX -h 127.0.0.1 -p 5432 -U hindsight -d hindsight -c select 1"
    ],
    "systemctl": [
        "hindsight-api.service"
    ],
    "dosyalar": {
        "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL": "DEĞİŞTİ",
        "root/sir-yedek-TS-db/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL": "YENİ",
        "run/credentials/hindsight-api.service/HINDSIGHT_API_DATABASE_URL": "YENİ",
        "run/credentials/hindsight-api.service/HINDSIGHT_API_LLM_API_KEY": "YENİ",
        "run/credentials/hindsight-api.service/HINDSIGHT_API_TENANT_API_KEY": "YENİ"
    },
    "stdout": [
        "=== ROTASYON: Postgres 'hindsight' rol parolası ===",
        "  ✓ yedek: /etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL",
        "  yedek dizini: <T>/kok/root/sir-yedek-TS-db",
        "  ✓ yeni değer üretildi (b64, 48 karakter; DEĞER BASILMAZ)",
        "  ✓ ALTER ROLE hindsight uygulandı · SQL dosyası silindi (parola argv'ye girmedi)",
        "  ✓ yazıldı: /etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL (YALNIZ parola alanı; kullanıcı/host/port/db/query korundu)",
        "-- yeniden başlat: hindsight-api.service",
        "  ✓ credential dolu: /run/credentials/hindsight-api.service/HINDSIGHT_API_DATABASE_URL (144 bayt)",
        "  ✓ hazır: hindsight-api N s",
        "  ✓ kanıt ucu DSN'den türetildi: hindsight@127.0.0.1:5432/hindsight (parola BASILMAZ)",
        "  ✓ yeni parola: select 1 → 1",
        "  ✓ eski parola: FATAL (kanıt parolaya BAĞLI)",
        ">> geri alma: eski parolayı ALTER ROLE ile geri koy + <T>/kok/root/sir-yedek-TS-db altındaki DSN'i geri yaz"
    ],
    "stderr": [
        ">> GERİ ALMA (bu koşum YEDEK aldı — başarıda da arızada da geçerli):",
        "     sudo cp -p <T>/kok/root/sir-yedek-TS-db/<yol> /<yol>   (yedek ağacı üretim yollarını AYNEN taşır)",
        "     sonra yeniden başlat: hindsight-api.service"
    ]
}


@pytest.mark.parametrize("etiket,args", [("kuru", ("--db", "--kuru")), ("gercek", ("--db",))],
                         ids=["kuru", "gercek"])
def test_C7_ESKI_DB_yolu_DEGISMEDI_altin_iz_ile_BIREBIR(tmp_path, etiket, args):
    altin = {"kuru": ALTIN_DB_KURU, "gercek": ALTIN_DB_GERCEK}[etiket]
    assert altin, "altın iz boş — pozitif kontrol (ayrıştırıcı boşa kıyaslamasın)"
    iz = _db_izi(BETIK, tmp_path / etiket, *args)
    assert iz == altin, json.dumps(iz, ensure_ascii=False, indent=1)


def test_C7b_ESKI_DB_yolunun_UYARISI_artik_BAGLI_sinifta_ve_KASA_YOLUNU_gosterir(tmp_path):
    """Bağın eski yoldaki TEK etkisi: uyarı sınıfı. Bağsız metnin "TASARLANMADI" cümlesi artık
    YANLIŞ olurdu (sıra bu dilimde tasarlandı) — bağlı sınıf doğru yolu (`--db --vault`) söyler."""
    _, ortam, _, _ = _db_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--db", "--kuru")
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    uy = v522._uyarilar(r.stdout)
    assert [(u["sinif"], u["sir"], u["yol"]) for u in uy] == [(v522.BAGLI_SINIF, DB_SIR, DB_HEDEF)], r.stdout
    assert f"sudo {BETIK} --db --vault" in uy[0]["blok"], uy[0]["blok"]
    assert "TASARLANMADI" not in r.stdout, r.stdout


# =================================================================================================
# Ç8 — ÖN KAPILAR + KANIT DÜŞERSE REÇETE
# =================================================================================================

@pytest.mark.parametrize("etiket,girdi,metin", [
    ("bos", "\n", "yapacak iş yok"),
    ("alfabe_disi", "SAHTE'YENI;PG\n", "SQL literaline uygun değil"),
    ("ayni_parola", f"{ESKI['pg']}\n", "ESKİ parolayla AYNI"),
], ids=["bos", "alfabe_disi", "ayni_parola"])
def test_C8_ON_KAPILAR_kasaya_DOKUNMADAN_durur_yedek_YOK(tmp_path, etiket, girdi, metin):
    kok, ortam, log, durum = _db_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--db", "--vault", girdi=girdi)
    assert r.returncode == 1, f"{etiket}: {r.returncode}\n{r.stdout}\n{r.stderr}"
    assert metin in r.stderr and "kasaya HİÇBİR ŞEY yazılmadı" in r.stderr, r.stderr
    o = _olaylar(kok)
    assert not [x for x in o if x.startswith(("kv-put", "alter", "restart", "kv-rollback"))], o
    assert _kasa(durum) == KASA_TOHUM and _pg(kok) == ESKI["pg"]
    assert not list((kok / "root").glob("sir-yedek-*")), "kapıda durulan koşum yedek aldı"
    _sir_yok(r, kok, log)


def test_C8b_KANIT_duserse_KASA_YOLUNUN_geri_alma_RECETESI_basilir(tmp_path):
    """ALTER 'kabul edildi' ama uygulanmadı: yeni parola bağlanamaz → ÖLÇÜLEMEDİ (çıkış 2). ALTER
    geri alınamaz bir kanaldır; reçete evreye göredir ve dosya kopyası ÖNERMEZ (Agent ezerdi)."""
    kok, ortam, log, durum = _db_ortami(tmp_path, SAHTE_ALTER_ETKISIZ="1")
    r = _kos(BETIK, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    assert r.returncode == 2, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "ALTER ROLE UYGULANDI" in r.stderr, r.stderr
    assert f"vault kv rollback -version={ESKI_SURUM} {DB_KASA}" in r.stderr, r.stderr
    assert f"restart {BIRIM}" in r.stderr, r.stderr
    assert "sudo cp -p" not in r.stderr, "kasa yolunda DOSYA kopyası reçetesi basıldı (Agent ezer)"
    _sir_yok(r, kok, log)


# =================================================================================================
# M — MUTASYONLAR (brief: beş mutasyon + yedek yol)
# =================================================================================================
#: Mutasyon ÇAPALARI — betiğin KENDİ metninden (`vault_db_rotasyon` · `_db_kasa_geri_al`); `_mutant`
#: her çapanın VAR olduğunu doğrular (bulunamayan çapa mutasyonsuz betik üretir, çivi hiçbir şey ölçmez).
PUT_CAPA = "  tr -d '\\r\\n' < \"$ISLIK/db_yeni_dsn\" | _vault kv put \"$yol\" value=- >/dev/null \\\n"
ALTER_CAPA = '  if ! _sql_kos "$sql"; then\n'
TAVAN_CAPA = '  if ! _render_bekle "$hedef" "$ISLIK/db_yeni_dsn"; then\n'
ALTER_GERI_CAPA = '    _db_kasa_geri_al || die "ALTER ROLE başarısız'
YEDEK_YOL_CAPA = ("    tr -d '\\r\\n' < \"$ISLIK/db_eski_dsn\" | _vault kv put \"$DB_KASA_YOL\" value=- "
                  ">/dev/null || return 1\n")


def test_M0_CAPALAR_betikte_TEKER_kez():
    metin = BETIK.read_text(encoding="utf-8")
    for capa in (PUT_CAPA, ALTER_CAPA, TAVAN_CAPA, ALTER_GERI_CAPA, YEDEK_YOL_CAPA):
        assert metin.count(capa) == 1, f"çapa {metin.count(capa)} kez: {capa!r}"


def test_M1_MUT_SIRA_TERS_ALTER_kasadan_ONCE_ise_C2_KIRMIZI(tmp_path):
    """ALTER kv put'un ÖNÜNE taşınır (tasarımın REDDETTİĞİ A sırası): Ç2'nin iki iddiası da düşer —
    sıra (alter < put) ve değişmez (ALTER koşarken render hedefi ESKİ parolayı taşır)."""
    m = _mutant(tmp_path, (ALTER_CAPA, "  if false; then\n"),
                (PUT_CAPA, '  _sql_kos "$sql"\n' + PUT_CAPA), ad="m1.sh")
    kok, ortam, _, _ = _db_ortami(tmp_path)
    r = _kos(m, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    o = _olaylar(kok)
    alter = [i for i, x in enumerate(o) if x.startswith("alter")]
    put = [i for i, x in enumerate(o) if x.startswith("kv-put")]
    assert alter and put and alter[0] < put[0], f"MUTASYON ISIRMADI:\n{o}\n{r.stdout}\n{r.stderr}"
    assert o[alter[0]] == "alter render=AYRI", o


def test_M2_MUT_render_TAVANINDA_ALTER_kosarsa_C3_KIRMIZI(tmp_path):
    """Bekleme tavana kadar SÜRER ama aşım yok sayılır: ALTER render kanıtı OLMADAN koşar."""
    m = _mutant(tmp_path, (TAVAN_CAPA, TAVAN_CAPA.replace(
        "  if ! _render_bekle", "  _render_bekle").replace("; then\n", " || true\n  if false; then\n")),
        ad="m2.sh")
    kok, ortam, _, durum = _db_ortami(tmp_path, SAHTE_RENDER="yok")
    r = _kos(m, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    o = _olaylar(kok)
    assert "alter render=AYRI" in o and _pg(kok) == YENI_PG, f"MUTASYON ISIRMADI:\n{o}\n{r.stdout}\n{r.stderr}"
    assert not [x for x in o if x.startswith("kv-rollback")], o


def test_M3_MUT_ALTER_dususunde_GERI_ALMA_yoksa_C4_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, (ALTER_GERI_CAPA, ALTER_GERI_CAPA.replace("_db_kasa_geri_al", ":")), ad="m3.sh")
    kok, ortam, _, durum = _db_ortami(tmp_path, SAHTE_ALTER_DUSER="1")
    r = _kos(m, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    o = _olaylar(kok)
    assert _kasa(durum)[-1] == YENI_DSN and not [x for x in o if x.startswith("kv-rollback")], (
        f"MUTASYON ISIRMADI:\n{o}\n{r.stderr}")
    # Mutant YALAN söyler ("kasa geri alındı") — Ç4'ün kasa ölçümü tam bunu yakalar.
    assert ALTER_DUSTU_METNI in r.stderr, r.stderr


def test_M4_MUT_DSN_stdouta_basilirsa_C5_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, (PUT_CAPA, '  cat "$ISLIK/db_yeni_dsn"\n' + PUT_CAPA), ad="m4.sh")
    kok, ortam, log, _ = _db_ortami(tmp_path)
    r = _kos(m, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    with pytest.raises(AssertionError, match="SIR DEĞERİ stdout"):
        _sir_yok(r, kok, log)


def test_M5_MUT_envanterden_ROTASYON_SIRI_silinirse_C6_KIRMIZI(tmp_path):
    def sok(veri):
        next(g for g in veri["vault_kv"] if g["ad"] == DB_KV).pop("rotasyon_siri")
    sahte = v521._sahte_envanter(tmp_path, "db_bagsiz", sok)
    (tmp_path / "c6").mkdir()
    with pytest.raises(AssertionError, match="rotasyon_siri"):
        _c6_denetle(sahte, tmp_path / "c6")
    # Davranış tarafı: aynı sahte envanterle kasa yolu durur (bağ davranışa iner).
    (tmp_path / "c6b").mkdir()
    _, ortam, log, _ = _db_ortami(tmp_path / "c6b", envanter=sahte)
    r = _kos(BETIK, ortam, "--db", "--vault", "--kuru")
    assert r.returncode == 1 and "kasaya BAĞLI sırrı YOK" in r.stderr, f"{r.stdout}\n{r.stderr}"


def test_M6_MUT_YEDEK_YOL_kalkarsa_C4b_KIRMIZI(tmp_path):
    """Rollback düşünce ESKİ DSN `kv put` ile geri yazılmazsa kasa YENİ DSN'de kalır."""
    m = _mutant(tmp_path, (YEDEK_YOL_CAPA, "    : || return 1\n"), ad="m6.sh")
    kok, ortam, _, durum = _db_ortami(tmp_path, SAHTE_ALTER_DUSER="1", SAHTE_ROLLBACK_KIRIK="1")
    r = _kos(m, ortam, "--db", "--vault", girdi=f"{YENI_PG}\n")
    assert _kasa(durum)[-1] == YENI_DSN and "KASA GERİ ALINAMADI" in r.stderr, (
        f"MUTASYON ISIRMADI:\n{_olaylar(kok)}\n{r.stderr}")

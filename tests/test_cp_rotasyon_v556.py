"""test_cp_rotasyon_v556.py — TSK-226b: CP erişim anahtarı için rotasyon yolu + iki betikte jeton argv'si
(2026-09-26).

NUMARA: `ls tests | grep _v556` boş (ana checkout + yedi worktree tarandı 2026-09-26; en yüksek v555,
`tsk204-alarm` ağacında).

BAĞLAM (Rol-1 brief'i, TSK-226 kaydı). `hindsight-cp.service` 2026-09-15..25 arasında iki sırrı root
`docker run` sürecinin argv'sinde taşıyordu (TSK-226 düzeltti: değersiz `-e AD`). Dağıtımdan sonra iki sır
döndürülecek: kiracı anahtarı `sir_rotasyon.sh --tenant --vault` ile (vardı). `HINDSIGHT_CP_ACCESS_KEY`
için alt komut YOKTU — ve değer ayrıca Rol-1'in bir tanımlama çıktısında oturum dökümüne düştü. Bu dosya
iki işi ölçer:

  İŞ 1 — `sir_rotasyon.sh --cp` (+ `--vault`, `--kuru`). Kopya kümesi envanterden türer (`--kopyalar`
    sözleşmesi, v447 A1/A2 + N10 eşitliği); kasa bağı `vault_kv.hindsight_cp_access_key.rotasyon_siri`.
    Kasa yolu KENDİ DALIDIR (`vault_cp_rotasyon`, `--db --vault` emsali): değer betik İÇİNDE üretilir
    (`_uret hex` — `--tenant` ile aynı sınıf, 64 hex, uzunluk denetimli; SORULMAZ, BASILMAZ), ESKİ değer
    KASADAN okunur, geri alma reçetesi EVREYE göredir (yedek · kasa · yayım; KV v2 sürümü).
    KANIT UCU — KAYNAKTAN ÖLÇÜLDÜ (vectorize-io/hindsight etiketi v0.9.2 = imaj pini 0.9.2, okundu
    2026-09-26): `hindsight-control-plane/src/app/api/auth/login/route.ts` `POST` gövdesi `{"key": …}`
    alır, `HINDSIGHT_CP_ACCESS_KEY` ile sabit-zamanlı kıyaslar → eşitse 200 `{"success": true}`
    (+ oturum çerezi), değilse 401; anahtar TANIMSIZSA 503; gövde JSON değilse 400. `src/middleware.ts`
    `/api/auth/` ve `/api/health`i kimliksiz (PUBLIC) geçirir; `src/app/api/health/route.ts` açıldıktan
    sonra HER ZAMAN 200 döner. A1'de ÖLÇÜLMEDİ (uydurma yasağı: 127.0.0.1:9999'da HTTP cevabı 2026-09-01'de
    A1'de ölçüldü — hazırlık ölçütü bu yüzden `http`, 200 değil).
  İŞ 2 — `deploy/hermes_api.sh` ve `deploy/verify_hermes_training.sh` pano jetonunu curl ARGV'sine koymaz:
    başlık `curl -H @-` ile STANDART GİRDİDEN verilir, `printf` kabuk YERLEŞİĞİDİR (süreç doğurmaz).
    Davranış (çıktı + çıkış kodu) ESKİ biçimle AYNI dünyada birebir kıyaslanır. Sınıf taraması
    (`deploy/**/*.sh` · `ops/**/*.sh`) başlık biçimli argv argümanlarında sır genişlemesini arar.

DÜZENEK — ŞİMLER YENİDEN YAZILMADI. v447 sahte kökü ve PATH şimleri (`_sahte_ortam`) aynen altta koşar;
bu dosya üstlerine YALNIZ şunları ekler:
  · `vault` — KV v2 sürüm modeli (v538 şiminin biçimi) + sahte Agent: kanonik hedefe VE yan dosyanın
    ilgili satırına render (eşleme envanterin `vault_kv` + `vault_dosyalar` bloklarından TÜRETİLİR —
    gerçek `agent.hcl` de oradan üretilir).
  · `systemctl` sarmalayıcısı — `restart hindsight-cp.service` anında konteynerin ETKİN anahtarını
    birimin `EnvironmentFile=` sırasıyla (birim + drop-in; `-` = yoksa atla; SONRAKİ kazanır) hesaplar.
    Sıra birim dosyalarından TÜRETİLİR. Sonra v447 şimine devreder (hazırlık bütçesi dahil).
  · `curl` sarmalayıcısı — `SIR_ROT_CP` kökündeki istekleri CP modeli (yukarıdaki kaynak ölçümü) ile
    cevaplar, ötekileri v447 şimine devreder. İstek günlüğüne YALNIZ başlık ADLARI ve "gövdede key var
    mı" (bool) yazılır.

BÖLÜMLER
  A  sözleşme — kopya kümesi envanterden · kasa bağı · tüketici · hazırlık ucu · değer üretim sınıfı
  B  kuru koşum — `--cp --kuru` ve `--cp --vault --kuru` (değer YOK, yazım YOK, restart YOK, kasa YOK)
  C  kasa yolu gerçek akış — sıra, üretim uzunluğu, değer basılmaz
  D  kanıt dalı — 2xx/401 ayrımı (sahte uç) · 503 · hazırlık · anahtar gövdede · eski yol iki dünya
  E  geri alma evreleri — kasa (render yok · put düşer) · yayım · ön kapı · sürüm doğruluğu
  G  İŞ 2 — iki betik: statik · dinamik ps (v552 deseni) · davranış eşitliği · sınıf taraması
  M  MUTASYONLAR — brief'in dört mutasyonu + hazırlık/gövde/evre (mutant tmp'ye yazılır)

SIR DEĞERİ YOK: her değer `SAHTE-` önekli ve sahtedir; üretilen değer test kökünde yaşar ve hiçbir çıktıya
girmediği ölçülür. ÇIKTI DİSİPLİNİ: kıyaslar önce BOOLEAN'a indirilir — iddia mesajları süreç tablosunu,
ortamı ya da değeri basmaz (yalnız ad).
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import threading

import pytest
import yaml

from tests import test_rotasyon_operator_mesajlari_v522 as v522
from tests import test_vault_dalga1_baglama_v521 as v521
from tests.test_hindsight_anahtar_argv_v552 import _torunlar
from tests.test_sir_rotasyon_v447 import (
    BETIK,
    ENVANTER,
    ESKI,
    _betik_kopyalari,
    _dosya_imzalari,
    _env_alan,
    _envanter_kopyalari,
    _kos,
    _sahte_ortam,
)

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]
URETICI = KOK_DEPO / "ops" / "vault_politika_uret.py"
CP_BIRIM = KOK_DEPO / "deploy" / "hindsight" / "hindsight-cp.service"
CP_DROPIN_DIZIN = KOK_DEPO / "deploy" / "hindsight" / "hindsight-cp.service.d"
HERMES_API = KOK_DEPO / "deploy" / "hermes_api.sh"
VERIFY = KOK_DEPO / "deploy" / "verify_hermes_training.sh"

SIR = "HINDSIGHT_CP_ACCESS_KEY"
KV_AD = "hindsight_cp_access_key"
KASA_YOLU = "secret/meridian/hindsight_cp_access_key"
KANON = "/etc/meridian/hindsight_cp_access_key"
ENV_CP = "/opt/hindsight/.env-cp"
ENV_CP_VAULT = "/opt/hindsight/.env-cp.vault"
BIRIM = "hindsight-cp.service"
CP_UC = "http://cp"                     # test kökünde CP'nin sahte host'u (SIR_ROT_CP)

ESKI_CP = "SAHTE-ESKI-CP-0556"
ONCEKI_CP = "SAHTE-ONCEKI-CP-0556"
KASA_TOHUM = [ONCEKI_CP, ESKI_CP]       # current_version = 2 → geri almanın hedefi
ESKI_SURUM = len(KASA_TOHUM)
JETON = "SAHTE-PANO-JETONU-0556"        # İŞ 2 — pano jetonu (x-meridian-token)

#: Hazırlık tavanı — CP tek birimdir; aşım çivileri (D5/M5) bu tavanı bekler.
CP_TAVAN_S = "2"


# =================================================================================================
# ŞİMLER — bu dosyanın EKLERİ (v447 şimleri aynen altta koşar)
# =================================================================================================
SIM_KASA = '''#!__PY__
"""KV v2 sürüm modeli + sahte Agent (kanonik hedef + yan dosya satırları). Değer YALNIZ stdin'den."""
import json, os, sys
DURUM = __DURUM__
ESLEME = __ESLEME__
YAN = __YAN__
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
    if os.environ.get("SAHTE_RENDER", "hep") != "hep":
        return
    deger = d[yol][-1]
    if yol in ESLEME:
        with open(KOK + ESLEME[yol], "w", encoding="utf-8") as fh:
            fh.write(deger)
    for dosya, alan, onek in YAN.get(yol, []):
        p = KOK + dosya
        satirlar = open(p, encoding="utf-8").read().splitlines(True) if os.path.exists(p) else []
        yeni = "%s=%s%s\\n" % (alan, onek, deger)
        for i, s in enumerate(satirlar):
            if s.startswith(alan + "="):
                satirlar[i] = yeni
                break
        else:
            satirlar.append(yeni)
        # Agent ROOT yazar (0400 dosyanın üzerine); şim root değildir → yan dosyaya yaz + os.replace
        # (dizin izni yeter), `perms = 0400` korunur.
        gecici = p + ".sim-render"
        with open(gecici, "w", encoding="utf-8") as fh:
            fh.write("".join(satirlar))
        os.chmod(gecici, 0o400)
        os.replace(gecici, p)
    olay("render %s v%d" % (yol, len(d[yol])))


def put_izin():
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
    print(json.dumps({"data": {"current_version": n}}))
    sys.exit(0)
if a[:2] == ["kv", "put"] and a[3:] == ["value=-"]:
    yol, deger = a[2], sys.stdin.read()
    if not put_izin():
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
    d = oku()
    d[yol].append(d[yol][surum - 1])
    yaz(d)
    olay("kv-rollback %s -version=%d v%d" % (yol, surum, len(d[yol])))
    render(yol, d)
    sys.exit(0)
sys.stderr.write("sim vault: tanınmayan çağrı: %s\\n" % a)
sys.exit(2)
'''

SIM_SYSTEMCTL_CP = '''#!__PY__
"""`restart hindsight-cp.service` → konteynerin ETKİN anahtarı birimin EnvironmentFile SIRASIYLA
(SONRAKİ kazanır; `-` işaretli dosya yoksa atlanır) hesaplanır ve `.sahte/cp_etkin`e yazılır."""
import os, sys
KOK = os.environ["SIR_ROT_KOK"]
DOSYALAR = __DOSYALAR__
a = sys.argv[1:]
if len(a) >= 2 and a[0] == "restart":
    with open(os.path.join(KOK, ".sahte", "argv.log"), "a", encoding="utf-8") as fh:
        fh.write("OLAY restart " + a[1] + "\\n")
    if a[1] == "hindsight-cp.service" and os.environ.get("SAHTE_CP_RESTART_ETKISIZ") != "1":
        etkin = ""
        for yol, secimli in DOSYALAR:
            try:
                satirlar = open(KOK + yol, encoding="utf-8").read().splitlines()
            except FileNotFoundError:
                if secimli:
                    continue
                raise
            for s in satirlar:
                if s.startswith("HINDSIGHT_CP_ACCESS_KEY="):
                    d = s.split("=", 1)[1].strip()
                    if len(d) >= 2 and d[0] == d[-1] and d[0] in chr(34) + chr(39):
                        d = d[1:-1]
                    etkin = d
        if os.environ.get("SAHTE_CP_ANAHTARSIZ") == "1":
            etkin = ""
        with open(os.path.join(KOK, ".sahte", "cp_etkin"), "w", encoding="utf-8") as fh:
            fh.write(etkin)
os.execv(__ASIL__, [__ASIL__] + a)
'''

SIM_CURL_CP = '''#!__PY__
"""`SIR_ROT_CP` kökündeki istekler → hindsight-control-plane 0.9.2 modeli; ötekiler v447 şimine."""
import json, os, re, sys
KOK = os.environ["SIR_ROT_KOK"]
CP = os.environ.get("SIR_ROT_CP", "")
ASIL = __ASIL__
a = sys.argv[1:]
if "-K" not in a or not CP:
    os.execv(ASIL, [ASIL] + a)
cfg = a[a.index("-K") + 1]
url = cikti = govde_yolu = None
basliklar = []
try:
    with open(cfg, encoding="utf-8") as fh:
        for satir in fh:
            m = re.match(r'(\\S+)\\s*=\\s*"(.*)"\\s*$', satir.strip())
            if not m:
                continue
            k, v = m.group(1), m.group(2)
            if k == "url":
                url = v
            elif k == "output":
                cikti = v
            elif k == "data-binary":
                govde_yolu = v[1:] if v.startswith("@") else v
            elif k == "header":
                basliklar.append(v.partition(": ")[0].lower())
except OSError:
    os.execv(ASIL, [ASIL] + a)
if not url or not url.startswith(CP + "/"):
    os.execv(ASIL, [ASIL] + a)
with open(os.path.join(KOK, ".sahte", "argv.log"), "a", encoding="utf-8") as fh:
    fh.write("curl " + " ".join(a) + "\\n")
with open(os.path.join(KOK, ".sahte", "url.log"), "a", encoding="utf-8") as fh:
    fh.write(url + "\\n")
if os.environ.get("SAHTE_UID", "1000") != "0":
    sys.stderr.write("curl: (26) couldn't open file\\n"); sys.exit(26)
if os.environ.get("SAHTE_CP_OLU") == "1":
    sys.stdout.write("000"); sys.stderr.write("curl: (7) Failed to connect\\n"); sys.exit(7)
butce = os.path.join(KOK, ".sahte", "butce_hindsight-cp.service")
try:
    kalan = int(open(butce).read() or 0)
except (OSError, ValueError):
    kalan = 0
if kalan > 0:
    with open(butce, "w") as fh:
        fh.write(str(kalan - 1))
    sys.stdout.write("000"); sys.stderr.write("curl: (7) Failed to connect\\n"); sys.exit(7)
yol = url[len(CP):]
govde, kod = "", "404"
if yol == "/api/health":
    kod, govde = "200", json.dumps({"status": "ok", "service": "hindsight-control-plane"})
elif yol == "/api/auth/login":
    try:
        etkin = open(os.path.join(KOK, ".sahte", "cp_etkin"), encoding="utf-8").read()
    except OSError:
        etkin = ""
    anahtar, gecerli_govde = None, False
    if govde_yolu is not None:
        try:
            anahtar = json.load(open(govde_yolu, encoding="utf-8")).get("key")
            gecerli_govde = True
        except (OSError, ValueError, AttributeError):
            gecerli_govde = False
    if not etkin:
        kod, govde = "503", json.dumps({"error": "Access key not configured"})
    elif not gecerli_govde:
        kod, govde = "400", json.dumps({"error": "Invalid request body"})
    elif os.environ.get("SAHTE_CP_KOR") == "1" or (anahtar and anahtar == etkin):
        kod, govde = "200", json.dumps({"success": True})
    else:
        kod, govde = "401", json.dumps({"error": "Invalid access key"})
    with open(os.path.join(KOK, ".sahte", "cp_istek.log"), "a", encoding="utf-8") as fh:
        fh.write("login basliklar=%s govdede_key=%s sonuc=%s\\n"
                 % (",".join(sorted(basliklar)) or "-", "EVET" if anahtar else "HAYIR", kod))
if cikti and cikti != "-":
    with open(cikti, "w", encoding="utf-8") as fh:
        fh.write(govde)
print(kod)
'''

SIM_OPENSSL_KISA = '''#!/bin/sh
# `openssl rand -hex 32` → 62 hane (bozuk üretim: PATH/konteyner kazası). Öteki çağrılar gerçek openssl.
if [ "$1" = "rand" ] && [ "$2" = "-hex" ]; then echo "abababababababababababababababababababababababababababababababab" | cut -c1-62; exit 0; fi
exec __ASIL__ "$@"
'''

_BAYRAKLAR = ("SAHTE_RENDER", "SAHTE_PUT_IZIN", "SAHTE_CP_KOR", "SAHTE_CP_OLU", "SAHTE_CP_ANAHTARSIZ",
              "SAHTE_CP_RESTART_ETKISIZ")


def _cp_env_dosyalari() -> list[tuple[str, bool]]:
    """Birimin `EnvironmentFile=` SIRASI — birim dosyası, sonra drop-in'ler (ad sırasıyla). systemd
    SONRAKİ dosyadaki aynı anahtarı geçerli sayar; `-` önekli yol yoksa atlanır. ELLE yazılmaz: şim
    birimin KENDİSİNİ modeller (drop-in kaldırılırsa model de değişir)."""
    out: list[tuple[str, bool]] = []
    for p in [CP_BIRIM, *sorted(CP_DROPIN_DIZIN.glob("*.conf"))]:
        for s in p.read_text(encoding="utf-8").splitlines():
            s = s.strip()
            if s.startswith("EnvironmentFile="):
                v = s[len("EnvironmentFile="):]
                out.append((v.lstrip("-"), v.startswith("-")))
    return out


def _kasa_eslemeleri() -> tuple[dict[str, str], dict[str, list[tuple[str, str, str]]]]:
    """Sahte Agent'ın render eşlemesi — envanterden (gerçek `agent.hcl` de oradan üretilir)."""
    veri = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    indeks = {g["ad"]: g for g in veri["vault_kv"]}

    def coz(ad: str) -> str:
        g = indeks[ad]
        return indeks[g["ayni_deger"]]["vault_yolu"] if g.get("ayni_deger") else g["vault_yolu"]

    esleme = {g["vault_yolu"]: g["hedef"] for g in veri["vault_kv"] if "hedef" in g}
    yan: dict[str, list[tuple[str, str, str]]] = {}
    for d in veri["vault_dosyalar"]:
        for s in d["satirlar"]:
            yan.setdefault(coz(s["sir"]), []).append(
                (d["yol"], s["alan"], "Bearer " if s["onek"] == "Bearer" else ""))
    return esleme, yan


def _cp_ortami(tmp_path: pathlib.Path, *, yan_dosya: bool = True, kasa: bool = True,
               **bayrak: str) -> tuple[pathlib.Path, dict, pathlib.Path, pathlib.Path]:
    """v447 sahte kök + CP dünyası (A1'in 2026-09-26 varsayılan hâli: kasa açık, Agent render ediyor,
    yan dosya kurulu, üç kopya EŞİT) + kasa/systemctl/curl ekleri."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / KANON.lstrip("/")).write_text(ESKI_CP, encoding="utf-8")   # Agent şablonu satır sonu yazmaz
    env_cp = kok / ENV_CP.lstrip("/")
    env_cp.write_text(f"HINDSIGHT_CP_ACCESS_KEY={ESKI_CP}\n"
                      f"HINDSIGHT_CP_DATAPLANE_API_KEY={ESKI['tenant']}\n", encoding="utf-8")
    env_cp.chmod(0o600)
    if yan_dosya:
        yd = kok / ENV_CP_VAULT.lstrip("/")
        yd.write_text(f"HINDSIGHT_CP_ACCESS_KEY={ESKI_CP}\n"
                      f"HINDSIGHT_CP_DATAPLANE_API_KEY={ESKI['tenant']}\n", encoding="utf-8")
        yd.chmod(0o400)
    (kok / ".sahte/cp_etkin").write_text(ESKI_CP, encoding="utf-8")
    durum = tmp_path / "kasa_v556.json"
    durum.write_text(json.dumps({KASA_YOLU: list(KASA_TOHUM)} if kasa else {}), encoding="utf-8")
    log = tmp_path / "kasa_v556_argv.log"
    esleme, yan = _kasa_eslemeleri()
    binn = tmp_path / "bin_v556"
    binn.mkdir()
    asil = tmp_path / "bin"          # v447 şimleri
    govdeler = {
        "vault": SIM_KASA.replace("__DURUM__", repr(str(durum))).replace("__ESLEME__", repr(esleme))
                         .replace("__YAN__", repr(yan)).replace("__KOK__", repr(str(kok)))
                         .replace("__LOG__", repr(str(log))),
        "systemctl": SIM_SYSTEMCTL_CP.replace("__DOSYALAR__", repr(_cp_env_dosyalari()))
                                     .replace("__ASIL__", repr(str(asil / "systemctl"))),
        "curl": SIM_CURL_CP.replace("__ASIL__", repr(str(asil / "curl"))),
    }
    for ad, govde in govdeler.items():
        (binn / ad).write_text(govde.replace("__PY__", sys.executable), encoding="utf-8")
        (binn / ad).chmod(0o755)
    jeton = kok / "etc/vault/admin.token"
    jeton.parent.mkdir(parents=True, exist_ok=True)
    jeton.write_text("SAHTE-hvs-yonetici\n", encoding="utf-8")
    ortam = dict(ortam, PATH=f"{binn}:{ortam['PATH']}", VAULT_BIN=str(binn / "vault"),
                 VAULT_TOKEN_FILE=str(jeton), VAULT_ENVANTER=str(ENVANTER),
                 VAULT_POLITIKA_URETICI=str(URETICI), PYTHON_BIN=sys.executable,
                 VAULT_RENDER_TAVAN_S="1", VAULT_RENDER_ARALIK_S="0.05", SIR_ROT_CP=CP_UC)
    for b in _BAYRAKLAR:
        ortam.pop(b, None)
    ortam.update(bayrak)
    return kok, ortam, log, durum


def _kasa(durum: pathlib.Path) -> list[str]:
    return json.loads(durum.read_text(encoding="utf-8")).get(KASA_YOLU, [])


def _olaylar(kok: pathlib.Path) -> list[str]:
    return [s[len("OLAY "):] for s in (kok / ".sahte/argv.log").read_text(encoding="utf-8").splitlines()
            if s.startswith("OLAY ")]


def _istekler(kok: pathlib.Path) -> list[str]:
    p = kok / ".sahte/cp_istek.log"
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def _etkin(kok: pathlib.Path) -> str:
    return (kok / ".sahte/cp_etkin").read_text(encoding="utf-8")


def _restartlar(kok: pathlib.Path) -> list[str]:
    return (kok / ".sahte/systemctl.log").read_text(encoding="utf-8").split()


def _ilk(olaylar: list[str], onek: str) -> int:
    for i, o in enumerate(olaylar):
        if o.startswith(onek):
            return i
    raise AssertionError(f"olay yok: {onek!r}")


def _yedek(kok: pathlib.Path) -> pathlib.Path:
    adaylar = sorted((kok / "root").glob("sir-yedek-*-cp"))
    assert len(adaylar) == 1, f"tam bir cp yedek dizini beklendi: {[a.name for a in adaylar]}"
    return adaylar[0]


def _mutant(tmp_path: pathlib.Path, *ciftler: tuple[str, str], ad: str = "mutant_v556.sh",
            kaynak: pathlib.Path = BETIK) -> pathlib.Path:
    """Mutasyona uğramış KOPYA — her çapa TEKİL olmak zorunda (bulunamayan ya da çoğul çapa sessizce
    yanlış yeri bozardı). Özgün dosya DEĞİŞMEZ."""
    metin = kaynak.read_text(encoding="utf-8")
    for eski, yeni in ciftler:
        assert metin.count(eski) == 1, f"mutasyon çapası tekil değil ({metin.count(eski)}): {eski!r}"
        metin = metin.replace(eski, yeni, 1)
    hedef = tmp_path / ad
    hedef.write_text(metin, encoding="utf-8")
    hedef.chmod(0o755)
    return hedef


def _deger_yok(r: subprocess.CompletedProcess, kok: pathlib.Path, *ekler: str,
               loglar: tuple[pathlib.Path, ...] = ()) -> None:
    """Değer ve sha256'sı (tam ya da ilk 8 hane) hiçbir yüzeyde yok. Mesajlar değeri BASMAZ (yalnız
    hangi yüzey, hangi tohum ADI)."""
    yuzeyler = {"stdout": r.stdout, "stderr": r.stderr}
    for ad in ("argv.log", "url.log", "cp_istek.log", "systemctl.log"):
        p = kok / ".sahte" / ad
        if p.exists():
            yuzeyler[ad] = p.read_text(encoding="utf-8")
    for log in loglar:
        if log.exists():
            yuzeyler[log.name] = log.read_text(encoding="utf-8")
    degerler = {"ESKI_CP": ESKI_CP, "ONCEKI_CP": ONCEKI_CP, **{f"ek{i}": d for i, d in enumerate(ekler)}}
    for etiket, metin in yuzeyler.items():
        for ad, d in degerler.items():
            sizdi = d in metin
            assert not sizdi, f"SIR DEĞERİ {etiket} içine düştü ({ad})"
            h = hashlib.sha256(d.encode()).hexdigest()
            hash_sizdi = h[:8] in metin
            assert not hash_sizdi, f"değerin HASH'i {etiket} içine düştü ({ad})"


# =================================================================================================
# A) SÖZLEŞME
# =================================================================================================

def test_A0_ITHAL_EDILEN_yollar_BU_AGACIN_dosyalari():
    """Worktree tuzağı (v520/v521 A0): ithal edilen modül başka ağaçtan yüklenirse bütün çiviler
    BAŞKA bir betiği ölçer — sessizce."""
    for yol in (BETIK, ENVANTER, pathlib.Path(v521.__file__), pathlib.Path(v522.__file__)):
        assert yol.resolve().is_relative_to(KOK_DEPO.resolve()), f"yabancı ağaçtan ithal: {yol}"


def test_A1_CP_kopyalari_ENVANTERDEN_ve_REFERANS_kanonik_render_hedefi():
    """Kopya kümesi TEK kaynaktan: betiğin `--kopyalar` çıktısındaki `cp` satırları envanterin
    `rotasyon_kopyalari` bloğuyla SIRASIYLA aynı (v447 A1/A2 küme, v520 A3 sıra ölçer; burada adıyla).
    REFERANS (ilk satır) Vault Agent'ın kanonik tek-değer kopyasıdır (d-1 emsali) — `.env-cp` satırı
    eski kanal KOPYASIDIR; kasa yan dosyası (`.env-cp.vault`) tabloda YOKTUR (onu yalnız Agent yazar)."""
    betik = [(k["alt"], k["sir"], k["tur"], k["yol"], k["alan"], k["onek"])
             for k in _betik_kopyalari() if k["alt"] == "cp"]
    envanter = [(k["alt_komut"], k["sir"], k["tur"], k["yol"], k.get("alan"), k.get("onek"))
                for k in _envanter_kopyalari() if k["alt_komut"] == "cp"]
    assert betik == envanter, (betik, envanter)
    assert betik == [("cp", SIR, "dosya", KANON, None, None),
                     ("cp", SIR, "env", ENV_CP, SIR, None)], betik
    assert not [k for k in _betik_kopyalari() if k["yol"] == ENV_CP_VAULT], "yan dosya tabloda"
    ham = subprocess.run(["bash", str(BETIK), "--kopyalar"], capture_output=True, text=True).stdout
    assert f"cp {SIR} dosya {KANON} - 0400 root:root -" in ham.splitlines()


def test_A2_KASA_BAGI_rotasyon_siri_kaynak_REFERANS_ve_tek_kv_satiri():
    """Bağın dört yüzü: `rotasyon_siri` · render hedefi = tablonun REFERANSI · `kaynak` = referans
    (`vault_sir_koy.sh` eşitlik kapısı; v520 A5 kuralı) · `kopya_kaynaklari` = kalan satır. Betiğin
    kasa satırı yardımcısı (`_vault_kv_satirlari`) TEK satır ve takma adsız döndürür."""
    kv = {g["ad"]: g for g in yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]}
    g = kv[KV_AD]
    assert g.get("rotasyon_siri") == SIR, g.get("rotasyon_siri")
    assert (g["vault_yolu"], g["hedef"]) == (KASA_YOLU, KANON), g
    assert g["kaynak"] == {"tur": "dosya", "dosya": KANON, "alan": None, "onek": None}, g["kaynak"]
    assert g["kopya_kaynaklari"] == [{"tur": "env_satiri", "dosya": ENV_CP, "alan": SIR, "onek": None}]
    r = v521._kv_satirlari(ENVANTER, SIR)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"{KV_AD}\t{KASA_YOLU}\t{KANON}\t{SIR}\t-"], r.stdout
    yd = next(d for d in yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_dosyalar"]
              if d["yol"] == ENV_CP_VAULT)
    assert {"alan": SIR, "sir": KV_AD, "onek": None} in yd["satirlar"], "yan dosya CP anahtarını taşımıyor"
    assert yd["yeniden_baslat"] == BIRIM


def test_A3_TUKETICI_ve_HAZIRLIK_UCU_tek_kaynaktan(tmp_path):
    """Tüketici = `hindsight-cp.service` (betiğin kuru raporundaki harita ↔ envanter `.service`
    kümesi). Hazırlık ucu `_hazir_uc` TEK tablosundadır: CP `/api/health` (kimliksiz; kaynak ölçümü) ve
    ölçüt `http` — 200 A1'de ÖLÇÜLMEDİ, HTTP cevabı ölçüldü (2026-09-01)."""
    _, ortam, _, _ = _cp_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--cp", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"    · {SIR} → {BIRIM}" in r.stdout.splitlines(), r.stdout
    envanterde = set()
    for k in _envanter_kopyalari():
        if k["sir"] == SIR:
            envanterde |= set(re.findall(r"[a-z0-9-]+\.service", k["tuketici"]))
    assert envanterde == {BIRIM}, envanterde
    kod = v521._fonksiyon("_hazir_uc")
    cikti = subprocess.run(["bash", "-c", kod + '\n_hazir_uc "$1"\n', "_", BIRIM], capture_output=True,
                           text=True, env=dict(os.environ, CP_KOK="http://cp-kok")).stdout.strip()
    assert cikti.split(" ", 2)[:2] == ["http://cp-kok/api/health", "http"], cikti


def test_A4_DEGER_URETIMI_tenant_SINIFI_iki_yolda_da_ve_DEGER_KAYNAGI_beyani_YOK():
    """Yeni değer `--tenant`in üretim sınıfıyla (`_uret hex` → `openssl rand -hex 32`, uzunluk 64
    denetimli) — eski yol (`cp_erisim`) VE kasa yolu (`vault_cp_rotasyon`) ikisi de üretir. Kasa yolu
    SORMADIĞI için `_deger_kaynagi_beyani` ("bu yol değeri ÜRETMEZ, sizden İSTER") cp'de SUSMALI."""
    for fn in ("cp_erisim", "vault_cp_rotasyon"):
        govde = v521._fonksiyon(fn)
        assert re.search(r"^\s*_uret hex\s*$", govde, re.M), f"{fn}: `_uret hex` çağrısı yok"
        assert "_oku_gizli" not in govde, f"{fn}: değer operatörden SORULUYOR"
    uret = v521._fonksiyon("_uret")
    assert "hex) openssl rand -hex 32 | tr -d '\\r\\n' > \"$cikti\"; hedef_uz=64 ;;" in uret
    kod = v521._fonksiyon("_deger_kaynagi_beyani") + '_deger_kaynagi_beyani "$1"\n'
    r = subprocess.run(["bash", "-c", kod, "_", "cp"], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == "", r.stdout


# =================================================================================================
# B) KURU KOŞUM
# =================================================================================================

def test_B1_ESKI_YOL_KURU_yazacagi_ve_baslatacagi_BIRIMI_soyler_UYARIYLA_hicbir_sey_yazmaz(tmp_path):
    kok, ortam, log, durum = _cp_ortami(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--cp", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    satirlar = r.stdout.splitlines()
    assert f"  yazılacak: {KANON}  (dosya, {SIR})" in satirlar, r.stdout
    assert f"  yazılacak: {ENV_CP}  ({SIR}=, önek=-)" in satirlar, r.stdout
    assert f"  yeniden başlatılacak: {BIRIM}" in satirlar, r.stdout
    assert any(s.startswith(f"    · hindsight-cp → {CP_UC}/api/health  kabul: ") for s in satirlar), r.stdout
    assert f"  kanıt: POST {CP_UC}/api/auth/login" in r.stdout, r.stdout
    # Kasaya BAĞLI sırrın eski yolu Agent render hedefine yazar → uyarı + doğru yol (v522 emsali).
    uy = v522._uyarilar(r.stdout)
    assert {(u["sir"], u["yol"]) for u in uy} == {(SIR, KANON)}, r.stdout
    assert all(u["sinif"] == v522.BAGLI_SINIF for u in uy), r.stdout
    assert f"sudo {BETIK} --cp --vault" in r.stdout, r.stdout
    assert _dosya_imzalari(kok) == once, "kuru koşum dosya yazdı"
    assert not _restartlar(kok) and not log.exists(), "kuru koşum restart/kasa çağrısı yaptı"
    assert _kasa(durum) == KASA_TOHUM
    _deger_yok(r, kok)


def test_B2_KASA_YOLU_KURU_plan_1_8_SIRAYLA_deger_URETILIR_SORULMAZ_hicbir_sey_yazmaz(tmp_path):
    kok, ortam, log, durum = _cp_ortami(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--cp", "--vault", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    # İlk satır kasa dağıtıcısının başlığıdır (`vault_rotasyon`, `--db --vault` ile aynı); plan onu izler.
    assert r.stdout.splitlines()[:2] == ["=== ROTASYON (KASADAN): --cp --vault ===",
                                         "=== KURU KOŞUM: --cp --vault (HİÇBİR ŞEY YAZILMADI, "
                                         "KASAYA DOKUNULMADI) ==="], r.stdout
    assert r.stdout.count("hazırlık hindsight-cp:") == 1, "hazırlık satırı birim TEKRARLI (tekilleştirme yok)"
    adimlar = [s for s in r.stdout.splitlines() if re.match(r"^  [1-8]\. ", s)]
    assert [s[2] for s in adimlar] == list("12345678"), adimlar
    plan = dict((s[2], s) for s in adimlar)
    assert KASA_YOLU in plan["1"] and "KASADAN" in plan["1"]
    assert "betik İÇİNDE üretilir" in plan["2"] and "SORULMAZ" in plan["2"] and "BASILMAZ" in plan["2"]
    assert "64" in plan["2"]
    assert f"sir-yedek-<UTC ts>-cp/vault/{KASA_YOLU}" in plan["3"]
    assert KASA_YOLU in plan["4"] and "rollback" in plan["4"]
    assert KANON in plan["5"]
    assert ENV_CP in plan["6"]
    assert BIRIM in plan["7"] and f"{CP_UC}/api/health" in plan["7"]
    assert f"POST {CP_UC}/api/auth/login" in plan["8"] and "401" in plan["8"]
    assert f"    · yan dosya: {ENV_CP_VAULT}" in r.stdout, r.stdout
    assert v522.DEGER_KAYNAGI not in r.stdout, "kasa yolu değeri ÜRETİYOR ama 'sizden İSTER' diyor"
    assert not v522._uyarilar(r.stdout), "kasa yolunda eski yol uyarısı basıldı"
    assert _dosya_imzalari(kok) == once, "kuru koşum dosya yazdı"
    assert not _restartlar(kok) and not log.exists(), "kuru koşum restart/kasa çağrısı yaptı"
    assert _kasa(durum) == KASA_TOHUM
    _deger_yok(r, kok)


# =================================================================================================
# C) KASA YOLU — GERÇEK AKIŞ
# =================================================================================================

def test_C1_KASA_YOLU_kasa_RENDER_eski_kanal_RESTART_kanit_SIRASIYLA_ve_hepsi_YENI(tmp_path):
    kok, ortam, log, durum = _cp_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--cp", "--vault", girdi="")   # stdin BOŞ: değer sorulmaz
    assert r.returncode == 0, r.stdout + r.stderr
    kasa = _kasa(durum)
    assert kasa[:2] == KASA_TOHUM and len(kasa) == 3, "kasaya TEK yeni sürüm yazılmadı"
    yeni = kasa[-1]
    assert (kok / KANON.lstrip("/")).read_text(encoding="utf-8").strip() == yeni, "render hedefi YENİ değil"
    assert _env_alan(kok / ENV_CP_VAULT.lstrip("/"), SIR) == yeni, "yan dosya YENİ değil (sahte Agent)"
    assert _env_alan(kok / ENV_CP.lstrip("/"), SIR) == yeni, "eski kanal `.env-cp` YENİ değerle yazılmadı"
    assert _env_alan(kok / ENV_CP.lstrip("/"), "HINDSIGHT_CP_DATAPLANE_API_KEY") == ESKI["tenant"], \
        "komşu satır (DATAPLANE) ezildi"
    assert _etkin(kok) == yeni, "CP YENİ anahtarla açılmadı"
    assert _restartlar(kok) == [BIRIM], _restartlar(kok)
    ol = _olaylar(kok)
    assert (_ilk(ol, "kv-get") < _ilk(ol, "kv-metadata") < _ilk(ol, "kv-put")
            < _ilk(ol, "render") < _ilk(ol, "restart")), ol
    assert f"CP /api/auth/login: yeni→200 · eski→401 (kanıt anahtara BAĞLI)" in r.stdout, r.stdout
    assert [i.split(" sonuc=")[1] for i in _istekler(kok)] == ["200", "401"], _istekler(kok)
    esit = [s for s in r.stdout.splitlines() if s.startswith(f"  {SIR} · ")]
    assert len(esit) == 2 and esit[0].endswith("→ VAR (referans kopya)") and esit[1].endswith("→ EŞİT"), esit
    assert re.search(r"✓ hazır: hindsight-cp \d+ s", r.stdout), r.stdout
    # Yedek: ESKİ değer (KASADAN) 0600 — geri almanın girdisi; eski kanal dosyası da yedekte.
    y = _yedek(kok)
    kasa_yedegi = y / "vault" / KASA_YOLU
    assert kasa_yedegi.read_text(encoding="utf-8").strip() == ESKI_CP
    assert stat.S_IMODE(kasa_yedegi.stat().st_mode) == 0o600
    assert _env_alan(y / ENV_CP.lstrip("/"), SIR) == ESKI_CP
    assert "başarıda da arızada da geçerli" in r.stderr and f"-version={ESKI_SURUM} {KASA_YOLU}" in r.stderr


def test_C2_DEGER_hicbir_ciktiya_argvye_gunluge_DUSMEZ(tmp_path):
    kok, ortam, log, durum = _cp_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 0, r.stdout + r.stderr
    _deger_yok(r, kok, _kasa(durum)[-1], loglar=(log,))


def test_C3_YENI_deger_64_hex_ve_iki_yolda_da_ESKI_ile_AYNI_DEGIL(tmp_path):
    kok, ortam, _, durum = _cp_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 0, r.stdout + r.stderr
    yeni = _kasa(durum)[-1]
    assert re.fullmatch(r"[0-9a-f]{64}", yeni), "kasa yolu değeri 64 küçük hex değil"
    kok2, ortam2, _, _ = _cp_ortami(tmp_path / "eski", yan_dosya=False)
    r2 = _kos(BETIK, ortam2, "--cp")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    yeni2 = _env_alan(kok2 / ENV_CP.lstrip("/"), SIR)
    assert re.fullmatch(r"[0-9a-f]{64}", yeni2 or ""), "eski yol değeri 64 küçük hex değil"
    assert yeni2 == (kok2 / KANON.lstrip("/")).read_text(encoding="utf-8").strip()
    assert "yeni değer üretildi (hex, 64 karakter; DEĞER BASILMAZ)" in r.stdout + r2.stdout


def test_C4_URETIM_KISA_ise_DURUR_kasaya_ve_dosyaya_HICBIR_SEY(tmp_path):
    """Uzunluk denetimi: `openssl` 62 hane verirse (PATH/konteyner kazası) kasaya yazılmaz."""
    kok, ortam, log, durum = _cp_ortami(tmp_path)
    kisa = tmp_path / "bin_kisa"
    kisa.mkdir()
    (kisa / "openssl").write_text(SIM_OPENSSL_KISA.replace("__ASIL__", subprocess.run(
        ["which", "openssl"], capture_output=True, text=True).stdout.strip()), encoding="utf-8")
    (kisa / "openssl").chmod(0o755)
    ortam["PATH"] = f"{kisa}:{ortam['PATH']}"
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "üretilen değer 62 karakter (beklenen 64)" in r.stderr, r.stderr
    assert _kasa(durum) == KASA_TOHUM and "kv-put" not in " ".join(_olaylar(kok))
    assert not _restartlar(kok)
    degisen = {y for y in set(once) | set(_dosya_imzalari(kok))
               if once.get(y) != _dosya_imzalari(kok).get(y) and "sir-yedek-" not in y}
    assert not degisen, degisen


# =================================================================================================
# D) KANIT DALI
# =================================================================================================

def test_D1_YUZEY_ANAHTARA_KOR_ise_ESKI_de_200_OLCULEMEDI_cikis_2(tmp_path):
    """`_farksal`in negatif ayağı: yüzey her anahtara 200 diyorsa (araya giren vekil, imaj değişimi)
    "yeni 200 döndü" hangi anahtarın geçerli olduğunu KANITLAMAZ → çıkış 2, "geçti" DEĞİL."""
    kok, ortam, _, _ = _cp_ortami(tmp_path, SAHTE_CP_KOR="1")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "CP /api/auth/login: ESKİ değerle HTTP 200" in r.stderr and "Kilit yürürlükte DEĞİL" in r.stderr
    assert "kanıt anahtara BAĞLI" not in r.stdout


def test_D2_CP_YENI_anahtari_ALMAZSA_yeni_401_OLCULEMEDI(tmp_path):
    """Restart konteyneri yeni değerle açmadıysa (ör. yan dosya eski, drop-in sırası ters) → yeni→401."""
    kok, ortam, _, _ = _cp_ortami(tmp_path, SAHTE_CP_RESTART_ETKISIZ="1")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "CP /api/auth/login: YENİ değerle HTTP 401 (beklenen 200)" in r.stderr, r.stderr


def test_D3_KONTEYNERDE_ANAHTAR_YOKSA_503_OLCULEMEDI(tmp_path):
    """Değersiz `-e AD` (TSK-226): değişken iki dosyada da yoksa docker onu konteynere HİÇ koymaz →
    CP girişi 503 ("Access key not configured"). Kilit KAPALI demektir; 'geçti' denemez."""
    kok, ortam, _, _ = _cp_ortami(tmp_path, SAHTE_CP_ANAHTARSIZ="1")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "YENİ değerle HTTP 503" in r.stderr, r.stderr


def test_D4_HAZIRLIK_CP_dinleyene_kadar_BEKLENIR_ve_sure_BASILIR(tmp_path):
    kok, ortam, _, _ = _cp_ortami(tmp_path, SAHTE_HAZIR_N="3")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(r"✓ hazır: hindsight-cp \d+ s", r.stdout), r.stdout
    saglik = [u for u in (kok / ".sahte/url.log").read_text().split() if u == f"{CP_UC}/api/health"]
    assert len(saglik) == 4, saglik


def test_D5_CP_HIC_ACILMAZSA_hazirlik_ASILIR_OLCULEMEDI(tmp_path):
    kok, ortam, _, _ = _cp_ortami(tmp_path, SAHTE_CP_OLU="1", HAZIR_BEKLE_TAVAN_S=CP_TAVAN_S)
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 2, r.stdout + r.stderr
    assert f"hazırlık bekleme aşıldı: {BIRIM} {CP_UC}/api/health → HTTP 000" in r.stderr, r.stderr
    assert not _istekler(kok), "hazır olmayan CP'ye kanıt isteği gitti"


def test_D6_ANAHTAR_istekte_GOVDEDE_baslikta_ve_argvde_DEGIL(tmp_path):
    kok, ortam, log, durum = _cp_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 0, r.stdout + r.stderr
    istekler = _istekler(kok)
    assert len(istekler) == 2, istekler
    for i in istekler:
        assert "basliklar=content-type " in i + " " and "govdede_key=EVET" in i, i
    argv = (kok / ".sahte/argv.log").read_text(encoding="utf-8")
    assert all(re.fullmatch(r"curl -K \S+", s) for s in argv.splitlines() if s.startswith("curl ")), \
        "curl argv'sinde -K dışında argüman var"
    _deger_yok(r, kok, _kasa(durum)[-1], loglar=(log,))


def test_D7_ESKI_YOL_kasa_CANLI_dunyada_UYARIR_ve_kanit_YENI_401_ile_DUSER(tmp_path):
    """Eski yol kanonik dosyayı + `.env-cp`yi yazar ama konteyner değeri KASA yan dosyasından alır
    (drop-in, SONRAKİ kazanır) → yeni→401, çıkış 2. Uyarı YAZIMDAN ÖNCE doğru yolu söylemişti."""
    kok, ortam, _, _ = _cp_ortami(tmp_path)
    r = _kos(BETIK, ortam, "--cp")
    assert r.returncode == 2, r.stdout + r.stderr
    assert r.stdout.index("!! UYARI — VAULT AGENT RENDER HEDEFİ") < r.stdout.index("yazıldı:"), r.stdout
    assert "YENİ değerle HTTP 401" in r.stderr, r.stderr


def test_D8_ESKI_YOL_kasasiz_dunyada_IKI_kopya_ESIT_restart_kanit_ve_YEDEK(tmp_path):
    kok, ortam, log, _ = _cp_ortami(tmp_path, yan_dosya=False)
    r = _kos(BETIK, ortam, "--cp")
    assert r.returncode == 0, r.stdout + r.stderr
    yeni = _env_alan(kok / ENV_CP.lstrip("/"), SIR)
    assert yeni != ESKI_CP and (kok / KANON.lstrip("/")).read_text().strip() == yeni
    assert _etkin(kok) == yeni and _restartlar(kok) == [BIRIM]
    assert "CP /api/auth/login: yeni→200 · eski→401 (kanıt anahtara BAĞLI)" in r.stdout, r.stdout
    assert _env_alan(_yedek(kok) / ENV_CP.lstrip("/"), SIR) == ESKI_CP
    assert not log.exists(), "eski yol kasaya dokundu"
    assert ">> GERİ ALMA (bu koşum YEDEK aldı" in r.stderr, "eski yolun genel reçetesi basılmadı"
    _deger_yok(r, kok, yeni)


# =================================================================================================
# E) GERİ ALMA EVRELERİ (kasa yolu)
# =================================================================================================

def test_E1_RENDER_GELMEZSE_evre_KASA_eski_kanal_YOK_restart_YOK_recete_SURUMLE(tmp_path):
    kok, ortam, _, durum = _cp_ortami(tmp_path, SAHTE_RENDER="yok")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "render bekleme aşıldı" in r.stderr
    assert _env_alan(kok / ENV_CP.lstrip("/"), SIR) == ESKI_CP, "render ölçülmeden eski kanal yazıldı"
    assert not _restartlar(kok) and _etkin(kok) == ESKI_CP
    assert len(_kasa(durum)) == 3, "kasa yazımı modellenmedi (pozitif kontrol)"
    assert ">> GERİ ALMA (--cp --vault): kasaya YENİ değer" in r.stderr, r.stderr
    assert f"vault kv rollback -version={ESKI_SURUM} {KASA_YOLU}" in r.stderr, r.stderr
    assert "YENİDEN BAŞLATILMAMALI" in r.stderr
    assert "sudo cp -p" not in r.stderr, "kasa evresinde dosya kopyası reçetesi (Agent ezer)"


def test_E2_KASA_YAZIMI_DUSERSE_die_evre_KASA_belirsizlik_ADIYLA(tmp_path):
    kok, ortam, _, durum = _cp_ortami(tmp_path, SAHTE_PUT_IZIN="0")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "kasaya yazılamadı" in r.stderr and "DENENDİ" in r.stderr, r.stderr
    assert _kasa(durum) == KASA_TOHUM and not _restartlar(kok)


def test_E3_KANIT_DUSERSE_evre_YAYIM_dort_adim_recete(tmp_path):
    kok, ortam, _, _ = _cp_ortami(tmp_path, SAHTE_CP_KOR="1")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 2
    recete = r.stderr[r.stderr.index(">> GERİ ALMA (--cp --vault"):]
    y = _yedek(kok)
    for parca in (f"1) kasa: vault kv rollback -version={ESKI_SURUM} {KASA_YOLU}",
                  f"2) render: {KANON}",
                  f"3) eski kanal: sudo cp -p {y}{ENV_CP} {ENV_CP}",
                  f"4) sudo systemctl restart {BIRIM}"):
        assert parca in recete, (parca, recete)
    assert recete.index("1) kasa") < recete.index("2) render") < recete.index("3) eski kanal") \
        < recete.index("4) sudo systemctl")


def test_E4_ON_KAPI_kasada_ESKI_deger_YOKSA_durur_yedek_ve_recete_YOK(tmp_path):
    kok, ortam, log, durum = _cp_ortami(tmp_path, kasa=False)
    r = _kos(BETIK, ortam, "--cp", "--vault")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "ESKİ değer kasadan okunamadı" in r.stderr and "HİÇBİR ŞEY yazılmadı" in r.stderr, r.stderr
    assert ">> GERİ ALMA" not in r.stderr
    assert not list((kok / "root").glob("sir-yedek-*")) and not _restartlar(kok)
    assert "kv-put" not in " ".join(_olaylar(kok))


def test_E5_RECETEDEKI_SURUM_gercekten_ESKI_degeri_geri_getirir(tmp_path):
    """Reçete bir METİN değil bir KOMUTTUR: basılan `-version=` sahte kasada uygulanınca kasadaki son
    değer ESKİ değer olmalı (bir önceki sürüm değil)."""
    kok, ortam, _, durum = _cp_ortami(tmp_path, SAHTE_RENDER="yok")
    r = _kos(BETIK, ortam, "--cp", "--vault")
    m = re.search(r"vault kv rollback (-version=\d+) (\S+)", r.stderr)
    assert m, r.stderr
    g = subprocess.run([ortam["VAULT_BIN"], "kv", "rollback", m.group(1), m.group(2)],
                       env=dict(ortam, SAHTE_RENDER="hep"), capture_output=True, text=True)
    assert g.returncode == 0, g.stderr
    assert _kasa(durum)[-1] == ESKI_CP, "reçetedeki sürüm ESKİ değeri geri getirmiyor"


# =================================================================================================
# G) İŞ 2 — İKİ BETİK: JETON ARGV'DE DEĞİL
# =================================================================================================

#: ESKİ BİÇİM = bu dilimden ÖNCEKİ satırlar (a7cbc06e). Mutasyon (M3) ve davranış eşitliği (G4) bu
#: tersine çevirmeyle kurulur: yeni betikteki çapalar eski satırlara geri çevrilir. Çapa sayıları pinli.
HERMES_ESKIYE = (
    ('H=(); [ -n "$TOKEN" ] && H=(-H @-)', 'H=(); [ -n "$TOKEN" ] && H=(-H "x-meridian-token: ${TOKEN}")', 1),
    ("jeton | curl -fsS", "curl -fsS", 5),
)
VERIFY_ESKIYE = (
    ("  AJ=$(printf 'x-meridian-token: %s\\n' \"${MERIDIAN_DASH_TOKEN}\" \\\n"
     "        | curl -s -H @- http://127.0.0.1:8080/api/hermes 2>/dev/null || true)",
     '  AJ=$(curl -s -H "x-meridian-token: ${MERIDIAN_DASH_TOKEN}" \\\n'
     "        http://127.0.0.1:8080/api/hermes 2>/dev/null || true)", 1),
)


def _eski_bicim(betik: pathlib.Path, ciftler, hedef: pathlib.Path) -> pathlib.Path:
    metin = betik.read_text(encoding="utf-8")
    for yeni, eski, adet in ciftler:
        assert metin.count(yeni) == adet, f"{betik.name}: çapa sayısı {metin.count(yeni)} ≠ {adet}: {yeni!r}"
        metin = metin.replace(yeni, eski)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(metin, encoding="utf-8")
    hedef.chmod(0o755)
    return hedef


def test_G1_STATIK_iki_betikte_baslik_STDINden_ve_printf_YERLESIK():
    for betik in (HERMES_API, VERIFY):
        kod = "\n".join(s for s in betik.read_text(encoding="utf-8").splitlines()
                        if not s.lstrip().startswith("#"))
        argvde = re.search(r"""-H\s+["'][^"'@]*\$""", kod) is not None
        assert not argvde, f"{betik.name}: başlık argümanında değişken genişlemesi (argv)"
        assert "-H @-" in kod, f"{betik.name}: başlık STDIN'den verilmiyor"
        assert "printf 'x-meridian-token: %s\\n'" in kod, f"{betik.name}: başlık printf ile üretilmiyor"
    # `printf` bash'te YERLEŞİKTİR: süreç doğurmaz, değer hiçbir argv'ye girmez.
    r = subprocess.run(["bash", "-c", "type -t printf"], capture_output=True, text=True)
    assert r.stdout.strip() == "builtin", r.stdout


@pytest.fixture
def pano():
    """Sahte pano (127.0.0.1:<rastgele>). İstek ANINDA kanca koşar (ps görüntüsü); yetki yalnız
    `x-meridian-token` EŞİTLİĞİYLE — değer hiçbir yere yazılmaz, yalnız bool."""
    durum = {"kanca": None, "istekler": []}

    class _Isleyici(http.server.BaseHTTPRequestHandler):
        def _cevap(self):
            if durum["kanca"] is not None:
                durum["kanca"]()
            yetkili = self.headers.get("x-meridian-token") == JETON
            durum["istekler"].append((self.command, self.path, yetkili,
                                      "x-meridian-token" in self.headers))
            if self.path in ("/healthz",):
                kod, govde = 200, b'{"status": "ok"}'
            elif self.path == "/metrics":
                kod, govde = 200, b"meridian_up 1\n"
            elif self.path.startswith("/api/"):
                kod, govde = (200, b'{"ok": true, "yol": "' + self.path.encode() + b'"}') if yetkili \
                    else (401, b'{"detail": "unauthorized"}')
            else:
                kod, govde = 404, b"{}"
            self.send_response(kod)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(govde)))
            self.end_headers()
            self.wfile.write(govde)

        do_GET = _cevap
        do_POST = _cevap

        def log_message(self, *a):  # sessiz-yutma: sahte sunucunun erişim günlüğü test çıktısını kirletmesin
            return

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Isleyici)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    durum["port"] = srv.server_address[1]
    yield durum
    srv.shutdown()
    srv.server_close()


def _torun_argvleri_goruntusu() -> tuple[int, list[str]]:
    r = subprocess.run(["ps", "-A", "-ww", "-o", "pid=,ppid=,args="], capture_output=True, text=True,
                       timeout=30)
    tablo = {}
    for satir in r.stdout.splitlines():
        p = satir.split(None, 2)
        if len(p) >= 2:
            tablo[p[0]] = (p[1], p[2] if len(p) > 2 else "")
    return r.returncode, [tablo[p][1] for p in _torunlar(tablo)]


def _hermes(betik: pathlib.Path, port: int, *arg: str, token: str | None = JETON):
    ortam = dict(os.environ, BASE=f"http://127.0.0.1:{port}")
    ortam.pop("TOKEN", None)
    if token is not None:
        ortam["TOKEN"] = token
    return subprocess.run(["bash", str(betik), *arg], capture_output=True, text=True, env=ortam, timeout=60)


ALT_KOMUTLAR = ("status", "reflect", "start", "stop", "skills")


@pytest.mark.parametrize("alt", ALT_KOMUTLAR)
def test_G2_DINAMIK_hermes_api_jeton_HICBIR_surecin_argvsinde_YOK_ve_baslik_ULASIR(pano, alt):
    goruntuler: list[tuple[int, list[str]]] = []
    pano["kanca"] = lambda: goruntuler.append(_torun_argvleri_goruntusu())
    r = _hermes(HERMES_API, pano["port"], alt)
    assert r.returncode == 0, r.stderr[-300:]
    assert goruntuler, "sunucuya istek gelmedi — süreç tablosu ölçülemedi"
    for kod, argvler in goruntuler:
        assert kod == 0
        gordu = any(f"127.0.0.1:{pano['port']}" in a for a in argvler)
        assert gordu, "POZİTİF KONTROL düştü: ps curl'ün argv'sini görmedi"
        sizan = sum(JETON in a for a in argvler)
        assert sizan == 0, f"jeton {sizan} sürecin argv'sinde"
    assert [i[2] for i in pano["istekler"]] == [True], "başlık sunucuya ULAŞMADI ya da yanlış değerle"


def test_G2b_JETON_BOSKEN_baslik_GONDERILMEZ(pano):
    r = _hermes(HERMES_API, pano["port"], "health", token=None)
    assert r.returncode == 0, r.stderr[-300:]
    assert [i[3] for i in pano["istekler"]] == [False]


VERIFY_SAHTE_CURL = '''#!__PY__
"""verify_hermes_training.sh için sahte curl: ÇAĞRI ANINDA süreç tablosu görüntüsü + stdin başlığı."""
import json, os, subprocess, sys
D = os.environ["SAHTE_VERIFY_DIZIN"]
a = sys.argv[1:]
n = len([x for x in os.listdir(D) if x.startswith("ps_")])
with open(os.path.join(D, "ps_%d.txt" % n), "w") as fh:
    fh.write(subprocess.run(["/bin/ps", "-A", "-ww", "-o", "pid=,ppid=,args="], capture_output=True,
                            text=True).stdout)
beklenen = os.environ.get("MERIDIAN_DASH_TOKEN")
baslik = None
if "@-" in a:
    for s in sys.stdin.read().splitlines():
        ad, _, deger = s.partition(": ")
        if ad.lower() == "x-meridian-token":
            baslik = deger
for i, x in enumerate(a[:-1]):
    if x == "-H" and a[i + 1].lower().startswith("x-meridian-token: "):
        baslik = a[i + 1].split(": ", 1)[1]
url = a[-1]
with open(os.path.join(D, "istek.log"), "a") as fh:
    fh.write("%s baslik=%s\\n" % (url, "YOK" if baslik is None else ("ESIT" if baslik == beklenen else "AYRI")))
if url.endswith("/api/hermes"):
    sys.stdout.write('{"autostart":true}' if baslik == beklenen else '{"detail":"unauthorized"}')
elif "%{http_code}" in a:
    sys.stdout.write("200")
'''


def _verify_dunyasi(tmp_path: pathlib.Path, betik: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """verify'nin KOPYASI tmp/deploy altında koşar (`cd "$(dirname "$0")/.."` → tmp): meridian içe
    aktarılmaz (sahte `python3` her çağrıda 1 döner), `pgrep` sahte (süreç yok), `curl` sahte."""
    kok = tmp_path / "dunya"
    hedef = kok / "deploy" / "verify_hermes_training.sh"
    hedef.parent.mkdir(parents=True)
    hedef.write_text(betik.read_text(encoding="utf-8"), encoding="utf-8")
    hedef.chmod(0o755)
    binn = tmp_path / "bin_verify"
    binn.mkdir()
    (binn / "python3").write_text("#!/bin/sh\nexit 1\n")
    (binn / "pgrep").write_text("#!/bin/sh\nexit 1\n")
    (binn / "curl").write_text(VERIFY_SAHTE_CURL.replace("__PY__", sys.executable))
    for ad in ("python3", "pgrep", "curl"):
        (binn / ad).chmod(0o755)
    kayit = tmp_path / "verify_kayit"
    kayit.mkdir()
    ortam = dict(os.environ, PATH=f"{binn}:{os.environ['PATH']}", MERIDIAN_DASH_TOKEN=JETON,
                 SAHTE_VERIFY_DIZIN=str(kayit))
    return hedef, ortam


def _verify_kos(hedef: pathlib.Path, ortam: dict):
    return subprocess.run(["bash", str(hedef)], capture_output=True, text=True, env=ortam, timeout=60)


def _verify_torun_argvleri(kayit: pathlib.Path) -> list[list[str]]:
    out = []
    for p in sorted(kayit.glob("ps_*.txt")):
        tablo = {}
        for satir in p.read_text().splitlines():
            q = satir.split(None, 2)
            if len(q) >= 2:
                tablo[q[0]] = (q[1], q[2] if len(q) > 2 else "")
        out.append([tablo[pid][1] for pid in _torunlar(tablo)])
    return out


def test_G3_DINAMIK_verify_jeton_argvde_YOK_baslik_ULASIR_ve_autostart_OLCULUR(tmp_path):
    hedef, ortam = _verify_dunyasi(tmp_path, VERIFY)
    r = _verify_kos(hedef, ortam)
    assert r.returncode == 0, r.stderr[-300:]
    kayit = pathlib.Path(ortam["SAHTE_VERIFY_DIZIN"])
    goruntuler = _verify_torun_argvleri(kayit)
    assert goruntuler, "sahte curl hiç çağrılmadı — ölçülemedi"
    gordu = any("127.0.0.1:8080/api/hermes" in a for g in goruntuler for a in g)
    assert gordu, "POZİTİF KONTROL düştü: ps curl'ün argv'sini görmedi"
    sizan = sum(JETON in a for g in goruntuler for a in g)
    assert sizan == 0, f"jeton {sizan} süreç argv'sinde"
    istek = (kayit / "istek.log").read_text()
    assert "http://127.0.0.1:8080/api/hermes baslik=ESIT" in istek, "başlık curl'e ULAŞMADI"
    assert "autostart ON, standalone loop yok" in r.stdout, "sunucu beyanı okunmadı (davranış)"


@pytest.mark.parametrize("alt,token", [(a, JETON) for a in ALT_KOMUTLAR]
                         + [("status", "SAHTE-YANLIS-JETON"), ("health", JETON), ("metrics", JETON),
                            ("bilinmeyen", JETON)])
def test_G4a_DAVRANIS_hermes_api_ESKI_bicimle_BIREBIR(pano, tmp_path, alt, token):
    eski = _eski_bicim(HERMES_API, HERMES_ESKIYE, tmp_path / "eski" / "hermes_api.sh")
    yeni_kopya = tmp_path / "yeni" / "hermes_api.sh"
    yeni_kopya.parent.mkdir()
    yeni_kopya.write_text(HERMES_API.read_text(encoding="utf-8"), encoding="utf-8")
    ry = _hermes(yeni_kopya, pano["port"], alt, token=token)
    re_ = _hermes(eski, pano["port"], alt, token=token)
    norm = (lambda s: s.replace(str(yeni_kopya), "<B>").replace(str(eski), "<B>"))
    assert (ry.returncode, norm(ry.stdout), norm(ry.stderr)) == (re_.returncode, norm(re_.stdout),
                                                                 norm(re_.stderr))
    assert len(pano["istekler"]) == (2 if alt != "bilinmeyen" else 0)
    assert pano["istekler"][0][2:] == pano["istekler"][1][2:] if pano["istekler"] else True


def test_G4b_DAVRANIS_verify_ESKI_bicimle_BIREBIR(tmp_path):
    yeni_h, ortam_y = _verify_dunyasi(tmp_path / "y", VERIFY)
    eski_kaynak = _eski_bicim(VERIFY, VERIFY_ESKIYE, tmp_path / "eski_kaynak" / "verify.sh")
    eski_h, ortam_e = _verify_dunyasi(tmp_path / "e", eski_kaynak)
    ry, re_ = _verify_kos(yeni_h, ortam_y), _verify_kos(eski_h, ortam_e)
    assert (ry.returncode, ry.stdout, ry.stderr) == (re_.returncode, re_.stdout, re_.stderr)
    assert "autostart ON" in ry.stdout


# ---- G5: SINIF TARAMASI — deploy/**/*.sh · ops/**/*.sh -------------------------------------------
#: Başlık/kimlik bayrakları: argümanı bir istek BAŞLIĞI ya da kimlik bilgisidir ve argv'ye girer.
KIMLIK_BAYRAKLARI = ("-H", "--header", "-u", "--user", "--oauth2-bearer", "--proxy-user",
                     "--password", "--http-password", "--proxy-password")
#: Yetki taşıyan başlık adı parçaları (küçük harf). `x-meridian-token` · `authorization` · `apikey` ·
#: `x-api-key` · `cookie` hepsi en az birini taşır.
YETKI_BASLIGI_PARCALARI = ("token", "auth", "key", "cookie", "secret", "pass", "session", "credential")
#: (depo-göreli dosya, başlık adı ya da değişken) → gerekçe (≥20 karakter). ÇÜRÜMEZ: kullanılmayan
#: kayıt kırmızıdır (G5a).
SINIF_ISTISNALARI: dict[tuple[str, str], str] = {
    ("deploy/oracle-a1/dash_token_credential.sh", "x-meridian-token"):
        "KAPSAM DIŞI BULGU 2026-09-26 (TSK-226b sınıf taraması): WP-H H3 tur-3 geçiş aracı jetonu "
        "`_auth_kodu \"$tok\"` ile KONUMSAL argümandan argv'ye koyuyor ve faz-1 sonunda YENİ jetonu "
        "terminale basıyor; `.dash.env` 2026-09-14'te silindi, `--dash` rotasyonu sir_rotasyon.sh'ta. "
        "Emekliye ayırma ya da düzeltme Rol-1 kararı (brief kapsamı iki betik).",
}
_GENISLEME = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*|[0-9@*])|([A-Za-z_][A-Za-z0-9_]*|[0-9@*]))")
_ARGUMAN = re.compile(r"""(?:^|[\s(;|&])(%s)(?:=|\s+)("(?:[^"\\]|\\.)*"|'[^']*'|[^\s;|&)]+)"""
                      % "|".join(re.escape(b) for b in KIMLIK_BAYRAKLARI))


def _sh_dosyalari(kok: pathlib.Path = KOK_DEPO) -> list[pathlib.Path]:
    out = []
    for taban in ("deploy", "ops"):
        for dizin, altlar, dosyalar in os.walk(kok / taban):
            altlar[:] = sorted(a for a in altlar if not a.startswith(".")
                               and a not in ("node_modules", "state", "backups", "__pycache__"))
            out += [pathlib.Path(dizin) / d for d in sorted(dosyalar) if d.endswith(".sh")]
    return out


def _mantiksal_satirlar(metin: str) -> list[str]:
    """`\\` devamları birleşir; tam-satır yorumlar atılır (satır içi `#` tırnak içinde olabilir —
    dokunulmaz, gürültülü yön)."""
    out, biriken = [], ""
    for s in metin.splitlines():
        if not biriken and s.lstrip().startswith("#"):
            continue
        if s.endswith("\\"):
            biriken += s[:-1] + " "
            continue
        out.append(biriken + s)
        biriken = ""
    if biriken:
        out.append(biriken)
    return out


def _sir_adi_mi(ad: str) -> bool:
    from tests.test_birim_argv_sir_v554 import _sir_adi_mi as v554_sir_adi_mi
    return v554_sir_adi_mi(ad)


def _sinif_tara(dosyalar: list[pathlib.Path], kok: pathlib.Path = KOK_DEPO
                ) -> tuple[list[tuple[str, str, str]], dict[str, int]]:
    """İhlal = (dosya, bayrak, ad) — ad: başlık adı (yetki başlığı) ya da değişken adı. Satır metni,
    değer TAŞINMAZ. Ölçüm sayaçları bedeli raporlar: kimlik bayrağı argümanı · genişleme taşıyan ·
    başlık dosyası (`@`) · ihlal."""
    ihlal: set[tuple[str, str, str]] = set()
    sayac = {"arguman": 0, "genislemeli": 0, "baslik_dosyasi": 0, "ihlal": 0}
    for p in dosyalar:
        try:
            goreli = p.resolve().relative_to(kok.resolve()).as_posix()
        except ValueError:  # sessiz-yutma: kök dışındaki (sentetik) dosya yalnız etikette görünür; hüküm etkilenmez
            goreli = p.name
        for satir in _mantiksal_satirlar(p.read_text(encoding="utf-8", errors="replace")):
            for m in _ARGUMAN.finditer(satir):
                bayrak, ham = m.group(1), m.group(2)
                sayac["arguman"] += 1
                deger = ham[1:-1] if ham[:1] in "\"'" and ham[-1:] == ham[:1] else ham
                if deger.startswith("@"):
                    sayac["baslik_dosyasi"] += 1
                    continue
                if ham.startswith("'"):
                    continue                      # tek tırnak: kabuk genişletmez (düz metin)
                adlar = [a or b for a, b in _GENISLEME.findall(deger)]
                if not adlar:
                    continue
                sayac["genislemeli"] += 1
                if bayrak in ("-H", "--header"):
                    baslik = deger.split(":", 1)[0].strip().lower() if ":" in deger else ""
                    if baslik and any(x in baslik for x in YETKI_BASLIGI_PARCALARI):
                        ihlal.add((goreli, bayrak, baslik))
                        continue
                    for ad in adlar:
                        if _sir_adi_mi(ad):
                            ihlal.add((goreli, bayrak, ad))
                elif bayrak in ("-u", "--user", "--proxy-user"):
                    # `kullanıcı:parola` biçimi — yalnız İKİ NOKTADAN SONRAKİ genişleme sırdır. `sudo -u
                    # "$X"` / `ps -u "$(id -u)"` (iki nokta yok) curl kimliği DEĞİLDİR: gürültü değil sessizlik.
                    sag = deger.split(":", 1)[1] if ":" in deger else ""
                    sag_adlar = [a or b for a, b in _GENISLEME.findall(sag)]
                    if sag_adlar:
                        ihlal.add((goreli, bayrak, sag_adlar[0]))
                else:
                    ihlal.add((goreli, bayrak, adlar[0]))
    sayac["ihlal"] = len(ihlal)
    return sorted(ihlal), sayac


def test_G5a_SINIF_deploy_ve_ops_sh_dosyalarinda_ARGVde_kimlik_basligi_YOK_istisnalar_BEYANLI():
    dosyalar = _sh_dosyalari()
    assert HERMES_API in dosyalar and VERIFY in dosyalar and BETIK in dosyalar, "kapsam kör"
    ihlaller, sayac = _sinif_tara(dosyalar)
    beyansiz = [i for i in ihlaller if (i[0], i[2]) not in SINIF_ISTISNALARI]
    assert not beyansiz, "argv'de kimlik başlığı (dosya · bayrak · AD): " + "; ".join(" · ".join(i) for i in beyansiz)
    kullanilan = {(i[0], i[2]) for i in ihlaller}
    curuk = [k for k in SINIF_ISTISNALARI if k not in kullanilan]
    assert not curuk, f"çürümüş istisna (artık ihlal yok — kaydı kaldır): {curuk}"
    assert all(len(g) >= 20 for g in SINIF_ISTISNALARI.values())
    assert sayac["arguman"] >= 1 and sayac["genislemeli"] >= 1, sayac   # pozitif kontrol: tarama bir şey gördü
    # BEDEL ÖLÇÜMÜ (yalnız sayılar — ad/değer yok): `-s` ile görünür; rapor bu satırdan okur.
    print(f"G5 ölçüm: dosya={len(dosyalar)} {sayac}")


def test_G5b_SINIF_TARAYICI_pozitif_ve_negatif_kontrol(tmp_path):
    ornekler = {
        "oter_1.sh": 'curl -s -H "x-meridian-token: ${MERIDIAN_DASH_TOKEN}" "$U"\n',
        "oter_2.sh": 'H=(); [ -n "$T" ] && H=(-H "Authorization: Bearer $T")\n',
        "oter_3.sh": 'f() {\n  curl -s -H "x-meridian-token: $1" "$API"\n}\n',
        "oter_4.sh": 'curl -u "admin:${ADMIN_PASS}" "$U"\n',
        "oter_5.sh": 'wget --header="X-API-KEY: $K" "$U"\n',
        "oter_6.sh": 'curl --oauth2-bearer "$ERISIM" \\\n  "$U"\n',
        "oter_7.sh": 'curl -H "X-Custom: $SERVIS_TOKEN" "$U"\n',
        "otmez_1.sh": "printf 'x-meridian-token: %s\\n' \"$T\" | curl -s -H @- \"$U\"\n",
        "otmez_2.sh": "curl -s -H 'apikey: bilerek-yanlis-anahtar' \"$U\"\n",
        "otmez_3.sh": 'curl -s -H "content-type: $CT" "$U"\n',
        "otmez_4.sh": "# curl -H \"x-meridian-token: $T\" (yorum)\n",
        "otmez_5.sh": 'curl -K "$cfg"\n',
        "otmez_6.sh": 'sudo -u "$KULLANICI_TOKEN_DIZIN" true; ps -u "$(id -u)" -o pid=\n',
    }
    for ad, metin in ornekler.items():
        (tmp_path / ad).write_text(metin, encoding="utf-8")
    ihlaller, _ = _sinif_tara(sorted(tmp_path.glob("*.sh")), kok=tmp_path)
    otenler = {i[0] for i in ihlaller}
    assert otenler == {a for a in ornekler if a.startswith("oter_")}, sorted(otenler)
    # Eski biçimli iki betik de öter (ölçümün bu dilimdeki hedefi).
    eski_h = _eski_bicim(HERMES_API, HERMES_ESKIYE, tmp_path / "e" / "hermes_api.sh")
    eski_v = _eski_bicim(VERIFY, VERIFY_ESKIYE, tmp_path / "e" / "verify_hermes_training.sh")
    ihlaller, _ = _sinif_tara([eski_h, eski_v], kok=tmp_path)
    assert {(i[0], i[2]) for i in ihlaller} == {("e/hermes_api.sh", "x-meridian-token"),
                                                ("e/verify_hermes_training.sh", "x-meridian-token")}


# =================================================================================================
# M) MUTASYONLAR — her çivinin hedeflediği dalı ısırdığının gösterimi (mutant tmp'de, özgün değişmez)
# =================================================================================================
ENV_SATIRI = f"cp {SIR} env {ENV_CP} {SIR} koru koru -\n"


def test_M1_MUT_kopya_listesinden_ENV_satiri_cikarsa_A1_ve_C1_KIRMIZI(tmp_path):
    m = _mutant(tmp_path, (ENV_SATIRI, ""))
    betik = [k for k in _betik_kopyalari(m) if k["alt"] == "cp"]
    envanter = [k for k in _envanter_kopyalari() if k["alt_komut"] == "cp"]
    assert len(betik) != len(envanter), "A1 ölçütü mutasyonu GÖRMEDİ"
    kok, ortam, _, _ = _cp_ortami(tmp_path / "d")
    r = _kos(m, ortam, "--cp", "--vault")
    assert _env_alan(kok / ENV_CP.lstrip("/"), SIR) == ESKI_CP, \
        f"mutasyon ISIRMADI: eski kanal yine yazıldı (C1 bu dalı ölçmüyor)\n{r.stdout}"


def test_M2_MUT_DEGER_basilirsa_C2_KIRMIZI(tmp_path):
    govde = v521._fonksiyon("vault_cp_rotasyon")
    capa = "\n  _uret hex\n"
    assert govde.count(capa) == 1, "çapa tekil değil"
    m = _mutant(tmp_path, (govde, govde.replace(capa, '\n  _uret hex\n  cat "$ISLIK/yeni"\n')))
    kok, ortam, _, durum = _cp_ortami(tmp_path / "d")
    r = _kos(m, ortam, "--cp", "--vault")
    yeni = _kasa(durum)[-1]
    assert yeni in r.stdout, "mutasyon ISIRMADI: değer basılmadı (sahne kurulmadı)"
    with pytest.raises(AssertionError):
        _deger_yok(r, kok, yeni)


@pytest.mark.parametrize("alt", ["status", "reflect"])
def test_M3_MUT_baslik_ARGVye_geri_konursa_G2_KIRMIZI(pano, tmp_path, alt):
    eski = _eski_bicim(HERMES_API, HERMES_ESKIYE, tmp_path / "hermes_api.sh")
    goruntuler: list[tuple[int, list[str]]] = []
    pano["kanca"] = lambda: goruntuler.append(_torun_argvleri_goruntusu())
    r = _hermes(eski, pano["port"], alt)
    assert r.returncode == 0, r.stderr[-300:]
    sizan = sum(JETON in a for _, argvler in goruntuler for a in argvler)
    assert sizan >= 1, "mutasyon ISIRMADI: eski biçimde de jeton argv'de görünmedi (G2 kör)"


def test_M3b_MUT_verify_baslik_ARGVye_geri_konursa_G3_KIRMIZI(tmp_path):
    eski_kaynak = _eski_bicim(VERIFY, VERIFY_ESKIYE, tmp_path / "k" / "verify.sh")
    hedef, ortam = _verify_dunyasi(tmp_path, eski_kaynak)
    _verify_kos(hedef, ortam)
    goruntuler = _verify_torun_argvleri(pathlib.Path(ortam["SAHTE_VERIFY_DIZIN"]))
    assert sum(JETON in a for g in goruntuler for a in g) >= 1, "mutasyon ISIRMADI (G3 kör)"


def test_M4_MUT_kanit_dali_HEP_BASARI_derse_D1_ve_D2_KIRMIZI(tmp_path):
    govde = v521._fonksiyon("_cp_kanit")
    m = _mutant(tmp_path, (govde, '_cp_kanit() {\n  oldu "CP /api/auth/login: yeni→200 · eski→401 '
                                  '(kanıt anahtara BAĞLI)"\n}\n'))
    for bayrak in ("SAHTE_CP_KOR", "SAHTE_CP_RESTART_ETKISIZ"):
        _, ortam, _, _ = _cp_ortami(tmp_path / bayrak, **{bayrak: "1"})
        r = _kos(m, ortam, "--cp", "--vault")
        assert r.returncode == 0, f"mutasyon ISIRMADI ({bayrak}): {r.returncode}\n{r.stderr[-400:]}"


def test_M5_MUT_CP_hazirlik_ucu_kalkarsa_D4_KIRMIZI(tmp_path):
    govde = v521._fonksiyon("_hazir_uc")
    satir = [s for s in govde.splitlines(True) if s.lstrip().startswith("hindsight-cp.service)")]
    assert len(satir) == 1, "çapa tekil değil"
    m = _mutant(tmp_path, (satir[0], ""))
    _, ortam, _, _ = _cp_ortami(tmp_path / "d", SAHTE_HAZIR_N="3")
    r = _kos(m, ortam, "--cp", "--vault")
    assert r.returncode == 2 and "YENİ değerle HTTP 000" in r.stderr, r.stderr[-400:]


def test_M6_MUT_anahtar_GOVDE_yerine_verilmezse_D6_KIRMIZI(tmp_path):
    govde = v521._fonksiyon("_cp_kanit")
    capa = '"200" "401 403" "key"'
    assert govde.count(capa) == 1
    m = _mutant(tmp_path, (govde, govde.replace(capa, '"200" "401 403"')))
    kok, ortam, _, _ = _cp_ortami(tmp_path / "d")
    r = _kos(m, ortam, "--cp", "--vault")
    assert r.returncode == 2 and "YENİ değerle HTTP 400" in r.stderr, r.stderr[-400:]
    assert all("govdede_key=HAYIR" in i for i in _istekler(kok))


def test_M7_MUT_KASA_evresi_atanmazsa_E1_recetesi_YANLIS(tmp_path):
    govde = v521._fonksiyon("vault_cp_rotasyon")
    capa = "  CP_KASA_EVRE=kasa\n"
    assert govde.count(capa) == 1
    m = _mutant(tmp_path, (govde, govde.replace(capa, "  :\n")))
    _, ortam, _, _ = _cp_ortami(tmp_path / "d", SAHTE_RENDER="yok")
    r = _kos(m, ortam, "--cp", "--vault")
    assert "vault kv rollback" not in r.stderr, "mutasyon ISIRMADI: reçete yine kasa evresinde"

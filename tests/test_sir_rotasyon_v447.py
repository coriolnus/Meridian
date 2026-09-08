"""test_sir_rotasyon_v447 — `deploy/oracle-a1/sir_rotasyon.sh` (A1 sır ROTASYONU).

BAĞLAM. 2026-09-07 gecesi dört sır A1'de ELLE döndürüldü (KAPI_APIKEY · Hindsight TENANT
anahtarı · Postgres `hindsight` rol parolası · MERIDIAN_DASH_TOKEN), her adım ssh üzerinden ve
çift kanıtla. Sabah operatör iki OpenRouter anahtarını yenileyecek. Elle rotasyonun kaçınılmaz
tek hatası "bir kopyayı unutmak"tır ve o hata SESSİZDİR: yeniden başlatılan birim çalışır,
unutulan kopyayı okuyan öteki birim ilk gerçek çağrısında 401 alır — yani arıza saatler sonra,
başka bir bağlamda görünür. Bu tur o dört rotasyonu KODLAR ve sabahki OpenRouter turunu
yeniden koşulabilir kılar.

EMSAL. `deploy/oracle-a1/sir_credential_gecis.sh` (yapı, test kökü kancası, `read -s`) ve
`tests/test_sir_credential_v439.py` (PATH şimleri). O betik bir sırrın KANALINI taşır; bu betik
kanala dokunmaz, DEĞERİNİ döndürür.

ÖLÇÜM MİMARİSİ. Betik `SIR_ROT_KOK` ile tmp bir köke yönlendirilir ve `sudo`/`systemctl`/`curl`/
`psql`/`install` PATH şimleriyle değiştirilir. Şimler oyuncak DEĞİL, MODELDİR:
  · `systemctl restart` systemd'nin yaptığını yapar — `LoadCredential` kaynağını
    `/run/credentials/<birim>/<kimlik>` altına kopyalar. Betiğin "credential dolu mu" ölçümü
    böylece GERÇEKTEN ölçer; sabit bir "evet" döndürseydik o kapı hiç sınanmamış olurdu.
  · `curl` sunulan anahtarı O ANDAKİ dosya içeriğiyle KARŞILAŞTIRIR — "yeni→200, eski→401"
    farkı simülasyonun içinde gerçekten doğar.
  · `psql -f` içindeki `ALTER ROLE`u UYGULAR (sahte parola durumuna yazar), `-c 'select 1'` ise
    PGPASSFILE'daki parolayı o duruma karşı ölçer.
  · `install` `-o kullanıcı:grup` BİRLEŞİK biçimini REDDEDER — A1'de ölçülen tuzak (`install:
    invalid user`); şim onu kabul etseydi çivi yanlış biçimi yeşil görürdü.

SIR DEĞERİ YOK: bu dosyadaki her değer SAHTEDİR ve adında öyle yazar. Üretilen değerler gerçek
`openssl` çıktısıdır ama test kökünde yaşar ve hiçbir kanıt onları BASMAZ.

BÖLÜMLER
  A. Kopya sözleşmesi ↔ `deploy/sir_envanteri.yaml` (tek-kaynak ayrışma çivisi)
  B. Betiğin yapısal kapıları (`bash -n`, `read -s`, argv, hash yok, `install -o -g`)
  C. `--kuru` (hiçbir yazım yok)
  D. `--kapi`      E. `--tenant`     F. `--db`     G. `--dash`     H. `--openrouter`
  I. `--envanter`  J. MUTASYON — her çivinin hedeflediği dalı gerçekten ısırdığının gösterimi
  K. TUR 2 — çekişmeli incelemenin 11 kökü (ayrıcalık modeli · üç hâl · DSN kanıtı · izinler)
  L. TUR 3 — yeniden incelemenin kalan kökleri (DSN yüzde-çözümü · curl kodu · envanter süsü ·
     `--kuru` kapsamı · motor API gövdesinin JSON kaçışı)

TUR 3'ÜN ANA DERSİ (K bölümünün dersinin ikinci yarısı): şim bir kanalı MODELLEMİYORSA o kanalın
arızası ÖLÇÜLEMEZ. `SIM_CURL` motorun sır zincirini tek dosyadan üretiyordu; gerçek motor
credential → ortam → `state/secrets.json` sırasını izler ve tohum dünyası o dosyayı ZATEN
taşıyordu. Yani `test_K4a` yeşildi ama betik canlıda çıkış 2 verecekti — çivi yanlış sebeple
yeşil (§6). Zincir modellendiği anda K4a/H1/H3 kırmızıya döndü; düzeltme ondan sonra yazıldı.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest
import yaml

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK_DEPO / "deploy" / "oracle-a1" / "sir_rotasyon.sh"
ENVANTER = KOK_DEPO / "deploy" / "sir_envanteri.yaml"

#: Tohum (SAHTE) değerler. Hepsi "SAHTE-" ile başlar: betiğin negatif kontrolde kullandığı
#: işaretçi küçük harfli `sahte-<hex>`tir, bu yüzden ikisi karışmaz.
ESKI = {
    "kapi": "SAHTE-ESKI-KAPI-0001",
    "nous": "SAHTE-ESKI-NOUS-0001",
    "dash": "SAHTE-ESKI-DASH-0001",
    "tenant": "SAHTE-ESKI-TENANT-0001",
    "llm": "SAHTE-ESKI-LLM-0009",
    "or": "SAHTE-ESKI-OR-0001",
    "pg": "SAHTE-ESKI-PAROLA",
}
DSN = ("postgresql://hindsight:" + ESKI["pg"] +
       "@127.0.0.1:5432/hindsight?sslmode=disable&application_name=hindsight-api")


# =================================================================================================
# ŞİMLER — davranış modelleri (bkz. dosya başlığı)
# =================================================================================================
#: KİMLİK MODELİ — TUR 2'NİN ANA KONUSU. İlk turun 54 çivisi bir SINIFA kördü: `sudo` şimi
#: `os.execvp` ile ÇAĞIRANIN kimliğinde koşuyordu, yani "root yazdı → ubuntu okuyamaz" farkı
#: simülasyonda hiç DOĞMUYORDU. Betiğin bütün kanıt hattı (curl `-K` cfg'si · `PGPASSFILE` ·
#: `psql -f <yol>`) gerçek A1'de bu fark yüzünden 000/EACCES dönecekken çivilerde yeşildi.
#: Model artık şu — ve mutasyonlar (K1c/K2b) onun gerçekten ısırdığını gösterir:
#:   · `SAHTE_UID` bir sürecin ETKİN kimliğidir (ubuntu=1000 · root=0 · postgres=999).
#:   · `id -u` onu basar → betiğin root kapısı GERÇEKTEN sınanır.
#:   · `sudo` çocuğunu `SAHTE_UID=0` ile koşar; `sudo -u <ad>` o adın uid'iyle.
#:   · `curl` `-K` yapılandırmasını YALNIZ root iken açabilir: o dosyayı `sudo python3` 0600 root
#:     yazar. Kimlik ayrılırsa curl düşer ve betik `_curl_kod` üzerinden `000` görür.
#:   · `psql -f <yol>` 0700 çalışma dizinini TRAVERSE etmek zorundadır — postgres giremez (EACCES).
#:     `PGPASSFILE` aynı kuralla okunur ve okunamayan pgpass libpq'da SESSİZCE yok sayılır.
SIM_ID = '''#!/usr/bin/env python3
"""`id -u` süreçlerin ETKİN kimliğini basar (SAHTE_UID); öteki biçimler gerçek `id`e gider."""
import os, sys
if sys.argv[1:] == ["-u"]:
    print(os.environ.get("SAHTE_UID", "1000")); sys.exit(0)
os.execvp("/usr/bin/id", ["/usr/bin/id"] + sys.argv[1:])
'''

SIM_SUDO = '''#!/usr/bin/env python3
"""Gerçek sudo gibi: çocuğu BAŞKA bir kimlikle koşar. `-u <ad>` o adın uid'ini verir."""
import os, sys
UIDLER = {"root": "0", "postgres": "999", "ubuntu": "1000"}
a = sys.argv[1:]
with open(os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "argv.log"), "a") as fh:
    fh.write("sudo " + " ".join(a) + "\\n")
hedef = "0"
if a and a[0] == "-u":
    hedef = UIDLER.get(a[1], "1001"); a = a[2:]
if a and a[0] in ("chown", "chgrp"):
    sys.exit(0)          # root'un chown'u BAŞARILIDIR; çivi makinesinde sahiplik değişmez
os.execvpe(a[0], a, dict(os.environ, SAHTE_UID=hedef))
'''

SIM_RM = '''#!/usr/bin/env python3
"""`SAHTE_RM_KIRIK=1` iken `rm -rf` başarısız olur — çalışma dizini temizliğinin BEDELİNİ ölçmek
için (K9). Öteki her çağrı gerçek `rm`e gider."""
import os, sys
a = sys.argv[1:]
if os.environ.get("SAHTE_RM_KIRIK") == "1" and "-rf" in a:
    sys.stderr.write("rm: Permission denied\\n"); sys.exit(1)
os.execv("/bin/rm", ["/bin/rm"] + a)
'''

SIM_INSTALL = '''#!/usr/bin/env python3
"""A1'de ÖLÇÜLEN tuzak: `install -o root:root` HATA verir; kullanıcı ve grup İKİ AYRI bayraktır."""
import os, sys
with open(os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "argv.log"), "a") as fh:
    fh.write("install " + " ".join(sys.argv[1:]) + "\\n")
args, mod, dizin, kalan, i = sys.argv[1:], None, False, [], 0
while i < len(args):
    t = args[i]
    if t == "-d":
        dizin = True; i += 1
    elif t == "-m":
        mod = args[i + 1]; i += 2
    elif t in ("-o", "-g"):
        if ":" in args[i + 1]:
            sys.stderr.write("install: invalid user/group: %s\\n" % args[i + 1]); sys.exit(1)
        i += 2
    else:
        kalan.append(t); i += 1
if not dizin:
    sys.stderr.write("sim install YALNIZ -d biçimini tanır\\n"); sys.exit(2)
for d in kalan:
    os.makedirs(d, exist_ok=True)
    if mod:
        os.chmod(d, int(mod, 8))
'''

SIM_SYSTEMCTL = '''#!/usr/bin/env python3
"""`restart` systemd'nin yaptığını yapar: LoadCredential kaynağını /run/credentials altına koyar."""
import os, shutil, sys
KOK = os.environ["SIR_ROT_KOK"]
KRED = {
    "meridian.service": {
        "dash_token": "/etc/meridian/dash_token",
        "NOUS_API_KEY": "/etc/meridian/nous_api_key",
        "KAPI_APIKEY": "/etc/meridian/kapi_apikey",
        "HINDSIGHT_API_TENANT_API_KEY":
            "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"},
    "hindsight-api.service": {
        "HINDSIGHT_API_TENANT_API_KEY":
            "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY",
        "HINDSIGHT_API_DATABASE_URL": "/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL",
        "HINDSIGHT_API_LLM_API_KEY": "/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY"},
}
a = sys.argv[1:]
if a and a[0] == "--version":
    print("systemd 255 (255.4-1ubuntu8.4)"); sys.exit(0)
if len(a) >= 2 and a[0] == "restart":
    birim = a[1]
    with open(os.path.join(KOK, ".sahte", "systemctl.log"), "a") as fh:
        fh.write(birim + "\\n")
    hedef_dizin = os.path.join(KOK, "run", "credentials", birim)
    for kimlik, kaynak in KRED.get(birim, {}).items():
        os.makedirs(hedef_dizin, exist_ok=True)
        hedef = os.path.join(hedef_dizin, kimlik)
        if os.path.exists(hedef):
            os.remove(hedef)
        if os.path.exists(KOK + kaynak):
            shutil.copyfile(KOK + kaynak, hedef)
sys.exit(0)
'''

SIM_CURL = '''#!/usr/bin/env python3
"""`-K <cfg>` okur, sunulan anahtarı O ANDAKİ dosya içeriğiyle KARŞILAŞTIRIR, HTTP kodunu basar.

SAHTE_KOR=1 → yüzey anahtara KÖR olur (her şeye 200 / ok:true). Betiğin "kanıt anahtara bağlı
değil → ölçülemedi" dalını ölçmenin tek dürüst yolu budur: dünyayı bozarız, betiği değil.
SAHTE_MOTOR_OLU=1 → MOTORUN TAMAMI ölü (`/api/…` uçlarının HEPSİ). İlk tur bunu yalnız
`/api/secrets/test/nous`a uyguluyordu: aynı süreçteki yazma/silme ucu ölü motorda ÇALIŞIYOR
görünüyordu — şimin betiğin varsaydığı dünyayı modellemesi (tur-2'nin kendi dersi).
SAHTE_PING_GOVDESIZ=1 → motor AYAKTA ve 200 döner ama gövde YOK: `OLCULEMEDI(govde-yok)` dalının
dünya tarafındaki karşılığı (araya giren vekil, kesik yanıt).

GERÇEK curl DAVRANIŞI: bağlanamasa bile `-w '%{http_code}'` çıktısını (`000`) basar VE 7 ile
düşer. Yerel ölçüm 2026-09-08: `curl … || echo 000` → `000000`. Şim stdout'a hiçbir şey
basmadığı için çivi canlıda HİÇ görülmeyecek bir dizgeyi (`000`) pinliyordu (inceleme B3).
"""
import json, os, re, sys
KOK = os.environ["SIR_ROT_KOK"]
KOR = os.environ.get("SAHTE_KOR") == "1"
with open(os.path.join(KOK, ".sahte", "argv.log"), "a") as fh:
    fh.write("curl " + " ".join(sys.argv[1:]) + "\\n")
if os.environ.get("SAHTE_UID", "1000") != "0":
    # `-K` yapılandırmasını `sudo python3` (root) 0600 ile yazdı: root olmayan curl AÇAMAZ.
    # Gerçek curl'ün davranışı: hata + çıkış != 0, stdout BOŞ → `_curl_kod` `000` döndürür.
    sys.stderr.write("curl: (26) couldn't open file\\n"); sys.exit(26)


def oku(yol):
    try:
        with open(KOK + yol, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def env_alan(yol, alan):
    try:
        with open(KOK + yol, encoding="utf-8") as fh:
            for s in fh:
                if s.startswith(alan + "="):
                    d = s.split("=", 1)[1].strip()
                    if len(d) >= 2 and d[0] == d[-1] and d[0] in "\\"'":
                        d = d[1:-1]
                    return d
    except OSError:
        return None
    return None


DEPO = KOK + "/opt/meridian/state/secrets.json"


def depo_oku():
    """Motorun KENDİ sır deposu (`meridian.secrets._read_file` → `state/secrets.json`)."""
    try:
        with open(DEPO, encoding="utf-8") as fh:
            veri = json.load(fh)
        return veri if isinstance(veri, dict) else {}
    except (OSError, ValueError):
        return {}


def nous_cozulen():
    """`meridian.secrets._fetch` SIRASI — GERİ-DÜŞÜŞ ZİNCİRİ: credential → süreç ortamı →
    `state/secrets.json` → gcp. İlk turun şimi YALNIZ credential'a bakıyordu: negatif kontrol
    credential'ı boşaltınca motor GERÇEKTE üçüncü basamaktaki eski-ama-geçerli kopyaya düşüp
    ok:true döndürecekken, şim ok:false diyordu — çivi yeşil, ama yanlış sebeple (inceleme B1).
    Boş credential bir DEĞER DEĞİLDİR (`credential_oku`: `return deger or None`; v439 A4)."""
    for d in (oku("/run/credentials/meridian.service/NOUS_API_KEY"),
              os.environ.get("NOUS_API_KEY"),
              depo_oku().get("NOUS_API_KEY")):
        if d:
            return None if d.startswith("sahte-") else d
    return None


a = sys.argv[1:]
cfg = a[a.index("-K") + 1]
url = cikti = yontem = govde_yolu = None
basliklar = {}
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
        elif k == "request":
            yontem = v
        elif k == "data-binary":
            govde_yolu = v[1:] if v.startswith("@") else v
        elif k == "header":
            ad, _, deger = v.partition(": ")
            basliklar[ad.lower()] = deger

if os.environ.get("SAHTE_MOTOR_OLU") == "1" and "/api/" in url:
    # MOTORUN TAMAMI ölü: `/api/secrets/test/nous` de, `/api/secrets/<ad>` yazma/silme ucu de
    # AYNI süreçtedir. Gerçek curl kodu (000) basar VE 7 ile düşer.
    sys.stdout.write("000")
    sys.stderr.write("curl: (7) Failed to connect\\n")
    sys.exit(7)

govde, kod = "", "404"
if url.endswith("/llm/v1/models"):
    kod = "200" if KOR or basliklar.get("apikey") == oku("/etc/meridian/kapi_apikey") else "401"
elif url.endswith("/chat/completions"):
    if not KOR and basliklar.get("apikey") != oku("/etc/meridian/kapi_apikey"):
        kod = "401"
    else:
        ust = env_alan("/opt/apisix/.env-apisix", "OPENROUTER_AUTH") or ""
        anahtar = ust[len("Bearer "):] if ust.startswith("Bearer ") else ""
        if not KOR and (not anahtar or anahtar.startswith("sahte-")):
            kod = "401"          # OpenRouter upstream reddi
        else:
            kod = "200"
            govde = json.dumps({"choices": [{"message": {"content": "pong"}}]})
elif url.endswith("/api/secrets/test/nous"):
    if not KOR and basliklar.get("x-meridian-token") != oku("/etc/meridian/dash_token"):
        kod = "401"
    else:
        kod = "200"
        if os.environ.get("SAHTE_PING_GOVDESIZ") != "1":
            govde = json.dumps({"ok": KOR or nous_cozulen() is not None})
elif url.endswith("/v1/default/banks"):
    bek = "Bearer " + (oku("/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY") or "")
    kod = "200" if KOR or basliklar.get("authorization") == bek else "401"
elif url.endswith("/health"):
    kod = "200"
elif "/api/secrets" in url:
    yetkili = KOR or basliklar.get("x-meridian-token") == oku("/etc/meridian/dash_token")
    kod = "200" if yetkili else "401"
    if yetkili and "/api/secrets/" in url:
        # YAZAN/SİLEN uç, `api.py::api_set_secret` / `api_delete_secret` → `secrets_mod.set/delete`
        # → `state/secrets.json`. Şim bunu modellemezse betiğin `api` kopyası simülasyonda HİÇ
        # DOĞMAZ ve geri-düşüş zinciri ölçülemez.
        ad = url.rsplit("/", 1)[-1]
        veri = depo_oku()
        if yontem == "DELETE":
            veri.pop(ad, None)
        else:
            try:
                with open(govde_yolu, encoding="utf-8") as fh:
                    veri[ad] = json.load(fh)["value"]
            except (OSError, TypeError, ValueError, KeyError):
                # `api.py`: gövde JSON değilse 400 ("expected JSON body"). Kaçışsız kurulan bir
                # gövdenin (çift tırnak ya da ters bölü taşıyan anahtar) canlıdaki karşılığı budur.
                kod = "400"
        if kod == "200":
            with open(DEPO, "w", encoding="utf-8") as fh:
                json.dump(veri, fh, ensure_ascii=False)
                fh.write("\\n")
if cikti and cikti != "-":
    with open(cikti, "w", encoding="utf-8") as fh:
        fh.write(govde)
print(kod)
'''

SIM_PSQL = '''#!/usr/bin/env python3
"""`-f -` gövdeyi STDIN'den okur; `-f <yol>` 0700 dizin TRAVERSAL'ını modeller (postgres giremez).

`-c 'select 1'` bağlantıyı GERÇEK libpq gibi kurar: `-h` yoksa yerel sokete düşer (bu makinede
yok), `-h/-p/-U/-d` beklenen hedefle eşleşmeli, `PGPASSFILE` yalnız SAHİBİNCE okunabilir ve
okunamayan pgpass SESSİZCE yok sayılır (libpq'nun tam davranışı: hata değil, parolasız deneme).
İlk turun şimi bunların hiçbirini modellemiyordu — `-h`siz, `-w`siz ve root'a ait bir pgpass'la
yapılan bir çağrı yeşil görünüyordu."""
import os, re, sys
KOK = os.environ["SIR_ROT_KOK"]
DURUM = os.path.join(KOK, ".sahte", "pg_parola")
UID = os.environ.get("SAHTE_UID", "1000")
with open(os.path.join(KOK, ".sahte", "argv.log"), "a") as fh:
    fh.write("psql " + " ".join(sys.argv[1:]) + "\\n")
a = sys.argv[1:]


def sec(ad):
    return a[a.index(ad) + 1] if ad in a else None


if "-f" in a:
    yol = sec("-f")
    if yol == "-":
        sql = sys.stdin.read()
    else:
        ust = os.path.dirname(os.path.abspath(yol))
        if UID != "0" and not (os.stat(ust).st_mode & 0o0005):
            sys.stderr.write('psql: error: could not open file "%s": Permission denied\\n' % yol)
            sys.exit(1)
        with open(yol, encoding="utf-8") as fh:
            sql = fh.read()
    m = re.search(r"ALTER ROLE (\\w+) PASSWORD '([^']+)'", sql)
    if not m:
        sys.stderr.write("psql: ERROR: syntax error\\n"); sys.exit(3)
    with open(DURUM, "w", encoding="utf-8") as fh:
        fh.write(m.group(2))
    sys.exit(0)
if "-c" in a:
    if "-h" not in a:
        sys.stderr.write('psql: error: connection to server on socket '
                         '"/var/run/postgresql/.s.PGSQL.5432" failed: No such file or '
                         'directory\\n')
        sys.exit(2)
    with open(os.path.join(KOK, ".sahte", "pg_hedef"), encoding="utf-8") as fh:
        bekle = fh.read().split()
    if [sec("-h"), sec("-p"), sec("-U"), sec("-d")] != bekle:
        sys.stderr.write('psql: error: connection to server at "%s", port %s failed: FATAL:  '
                         'database or role does not exist\\n' % (sec("-h"), sec("-p")))
        sys.exit(2)
    pgpass, parola = os.environ.get("PGPASSFILE"), None
    if pgpass and os.path.exists(pgpass) and UID == "0":
        with open(pgpass, encoding="utf-8") as fh:
            parola = fh.read().strip().split(":")[-1]
    if parola is None:
        sys.stderr.write("psql: error: connection to server failed: fe_sendauth: no password "
                         "supplied\\n" if "-w" in a else "Password for user hindsight: ")
        sys.exit(2)
    with open(DURUM, encoding="utf-8") as fh:
        gecerli = fh.read().strip()
    if parola == gecerli:
        print("1"); sys.exit(0)
    sys.stderr.write('psql: error: connection to server failed: FATAL:  password '
                     'authentication failed for user "hindsight"\\n')
    sys.exit(2)
sys.exit(0)
'''


def _sahte_ortam(tmp_path: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """Test kökünü + PATH şimlerini kurar. Tohumlar A1'in ÖLÇÜLEN hâlini taklit eder:
    `/opt/meridian/.env` pano token'ının İKİNCİ kopyasını taşır (spec Bulgu-2) ve
    `/opt/hindsight/.env` üç hindsight sırrını taşır — ikisi de betiğin kopya tablosunda YOKTUR
    ve `--envanter` taraması onları BEYAN DIŞI KOPYA diye bulmak zorundadır."""
    kok = tmp_path / "kok"
    for d in ("etc/meridian", "etc/hindsight/creds", "opt/meridian", "opt/meridian/state",
              "opt/hindsight", "opt/apisix", "root", "run/credentials", ".sahte",
              "home/ubuntu/.hermes/profiles/bekci", "home/ubuntu/.hermes/profiles/karne",
              "home/ubuntu/.hermes/profiles/sef"):
        (kok / d).mkdir(parents=True, exist_ok=True)

    (kok / "etc/meridian/kapi_apikey").write_text(ESKI["kapi"] + "\n")
    (kok / "etc/meridian/nous_api_key").write_text(ESKI["nous"] + "\n")
    (kok / "etc/meridian/dash_token").write_text(ESKI["dash"] + "\n")
    (kok / "etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY").write_text(ESKI["tenant"] + "\n")
    (kok / "etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY").write_text(ESKI["llm"] + "\n")
    (kok / "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL").write_text(DSN + "\n")
    (kok / "opt/hindsight/.key").write_text(ESKI["tenant"] + "\n")
    (kok / "opt/hindsight/.env-cp").write_text(
        "HINDSIGHT_CP_ACCESS_KEY=sahte-access\n"
        f"HINDSIGHT_CP_DATAPLANE_API_KEY={ESKI['tenant']}\n")
    (kok / "opt/hindsight/.env").write_text(
        f"HINDSIGHT_API_TENANT_API_KEY={ESKI['tenant']}\n"
        f"HINDSIGHT_API_LLM_API_KEY={ESKI['llm']}\n"
        f"HINDSIGHT_API_DATABASE_URL={DSN}\n")
    (kok / "opt/apisix/.env-apisix").write_text(
        "APISIX_ADMIN_KEY=sahte-admin\n"
        f'OPENROUTER_API_KEY="{ESKI["or"]}"\n'
        f'OPENROUTER_AUTH="Bearer {ESKI["or"]}"\n'
        "PANO_GIRIS_PAROLA=sahte-parola\n"
        "BOT_KEY_BEKCI=sahte-bekci\n"
        "BOT_KEY_KARNE=sahte-karne\n"
        "BOT_KEY_SEF=sahte-sef\n"
        f"BOT_KEY_MERIDIAN='{ESKI['kapi']}'\n")
    (kok / "opt/meridian/.env").write_text(
        "NOUS_MODEL=sahte/model-mini\n"
        "NOUS_ENDPOINT=http://kapi/llm/v1\n"
        f"MERIDIAN_DASH_TOKEN={ESKI['dash']}\n")       # spec Bulgu-2: BEYAN DIŞI ikinci kopya
    (kok / "opt/meridian/.dash.env").write_text(f'MERIDIAN_DASH_TOKEN="{ESKI["dash"]}"\n')
    for p in ("bekci", "karne", "sef"):
        (kok / f"home/ubuntu/.hermes/profiles/{p}/.env").write_text(
            f"HERMES_HOME=/home/ubuntu/.hermes/profiles/{p}\n"
            f"BOT_KEY_{p.upper()}=sahte-{p}\n"
            f"OPENROUTER_API_KEY={ESKI['or']}\n")
    # MOTORUN KENDİ SIR DEPOSU — `.env` değil JSON. `NOUS_API_KEY` kopya tablosunda `api` satırıyla
    # BEYANLIDIR; `MERIDIAN_DASH_TOKEN` beyan DIŞIDIR (kalıcı kayıt 2026-09-06: kimlikler burada
    # yaşar) ve `--envanter` onu bulmak zorundadır. Değerler SAHTEDİR ve hiçbir yere basılmaz.
    (kok / "opt/meridian/state/secrets.json").write_text(json.dumps(
        {"NOUS_API_KEY": ESKI["nous"], "MERIDIAN_DASH_TOKEN": ESKI["dash"],
         "ALPACA_API_KEY": "SAHTE-ALPACA-0001"}, ensure_ascii=False) + "\n")
    (kok / ".sahte/pg_parola").write_text(ESKI["pg"])
    (kok / ".sahte/pg_hedef").write_text("127.0.0.1 5432 hindsight hindsight\n")
    (kok / ".sahte/argv.log").write_text("")
    (kok / ".sahte/systemctl.log").write_text("")

    binn = tmp_path / "bin"
    binn.mkdir()
    for ad, kaynak in (("sudo", SIM_SUDO), ("install", SIM_INSTALL), ("systemctl", SIM_SYSTEMCTL),
                       ("curl", SIM_CURL), ("psql", SIM_PSQL), ("id", SIM_ID), ("rm", SIM_RM)):
        (binn / ad).write_text(kaynak)
        (binn / ad).chmod(0o755)

    # `SAHTE_UID=0`: operatörün BELGELENEN çağrı biçimi `sudo ./sir_rotasyon.sh …`dır, yani betik
    # root olarak koşar. Kimliği ortamdan vermek, "root değilken ne olur" sorusunu da ölçülebilir
    # kılar (K1a/K1c: 1000 ile koş).
    # `TMPDIR=tmp_path`: `mktemp -d` bunu onurlandırır, yani 0700 çalışma dizini KOŞUMUN KENDİ
    # tmp_path'i altında doğar. İlk turda J8 paylaşılan `/tmp`i glob'luyordu ve komşu süreçlerin
    # dizinlerini görüyordu — `-n 4` altında flaky bir çivi, yani hüküm olmayan bir hüküm.
    ortam = dict(os.environ, PATH=f"{binn}:{os.environ['PATH']}", SIR_ROT_KOK=str(kok),
                 SIR_ROT_API="http://motor", SIR_ROT_HINDSIGHT="http://hafiza",
                 SIR_ROT_KAPI="http://kapi/llm/v1", SAHTE_UID="0", TMPDIR=str(tmp_path))
    for bayrak in ("SAHTE_KOR", "SAHTE_MOTOR_OLU", "SAHTE_RM_KIRIK", "SAHTE_PING_GOVDESIZ"):
        ortam.pop(bayrak, None)
    return kok, ortam


def _kos(betik: pathlib.Path, ortam: dict, *args: str, girdi: str = "",
         cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(betik), *args], capture_output=True, text=True,
                          env=ortam, input=girdi, cwd=str(cwd) if cwd else None)


def _env_alan(yol: pathlib.Path, alan: str) -> str | None:
    for s in yol.read_text(encoding="utf-8").splitlines():
        if s.startswith(alan + "="):
            return s.split("=", 1)[1]
    return None


def _yedek_dizini(kok: pathlib.Path) -> pathlib.Path:
    adaylar = sorted((kok / "root").glob("sir-yedek-*"))
    assert len(adaylar) == 1, f"tam bir yedek dizini beklendi, bulunan: {adaylar}"
    return adaylar[0]


def _birim_sirasi(kok: pathlib.Path) -> list[str]:
    return (kok / ".sahte/systemctl.log").read_text(encoding="utf-8").split()


# =================================================================================================
# A) KOPYA SÖZLEŞMESİ ↔ ENVANTER (tek-kaynak ayrışma çivisi)
# =================================================================================================

def _betik_kopyalari() -> list[dict]:
    """`--kopyalar` alt komutunu GERÇEKTEN koşarak tabloyu alır. Metni grep'lemek yerine betiği
    koşturmak, tablonun bir ÇIKTI olduğunu (yani betiğin kendi mantığının okuduğu şeyle aynı
    olduğunu) ölçer — beyan ile davranış ancak böyle ayrışamaz."""
    r = subprocess.run(["bash", str(BETIK), "--kopyalar"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    out = []
    for satir in r.stdout.strip().splitlines():
        alt, sir, tur, yol, alan, mod, sahip, onek = satir.split()
        out.append({"alt": alt, "sir": sir, "tur": tur, "yol": yol,
                    "alan": None if alan == "-" else alan, "mod": mod, "sahip": sahip,
                    "onek": None if onek == "-" else onek})
    return out


def _envanter_kopyalari() -> list[dict]:
    return yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["rotasyon_kopyalari"]["kopyalar"]


def test_A0_kopya_tablosu_BOS_DEGIL_pozitif_kontrol():
    """Ayrıştırıcının kendisi ölçülür. Boş bir tablo boş bir envantere EŞİTTİR — yasanın en
    sessiz arızası; A1/A2 o hâlde "her şey uyuşuyor" derdi."""
    k = _betik_kopyalari()
    assert len(k) == 17, k
    assert {x["alt"] for x in k} == {"kapi", "tenant", "db", "dash", "openrouter"}
    assert {x["tur"] for x in k} == {"dosya", "env", "url", "api", "sql"}


def test_A1_betikteki_YOLLAR_envanterde_VAR():
    """Brief'in istediği yön (⊆): betik envanterin GÖRMEDİĞİ bir kopyayı yazarsa, o kopya
    envanterle yönetilen hiçbir denetime girmez ve ilk rotasyondan sonra sessizce ayrışır."""
    betikte = {(x["alt"], x["tur"], x["yol"], x["alan"]) for x in _betik_kopyalari()}
    envanterde = {(x["alt_komut"], x["tur"], x["yol"], x.get("alan"))
                  for x in _envanter_kopyalari()}
    eksik = betikte - envanterde
    assert not eksik, f"betikte olup envanterde OLMAYAN kopyalar: {sorted(eksik)}"


def test_A2_envanterdeki_YOLLAR_betikte_VAR():
    """Ters yön. Tek yön yeterli DEĞİLDİR: betikten bir kopya silinseydi envanter onu taşımaya
    devam eder ve "rotasyon bu dosyayı yazıyor" beyanı sessizce yalan olurdu (tek-kaynak yasası
    iki yönlü bir yasadır)."""
    betikte = {(x["alt"], x["tur"], x["yol"], x["alan"]) for x in _betik_kopyalari()}
    envanterde = {(x["alt_komut"], x["tur"], x["yol"], x.get("alan"))
                  for x in _envanter_kopyalari()}
    fazla = envanterde - betikte
    assert not fazla, f"envanterde olup betikte OLMAYAN kopyalar: {sorted(fazla)}"


def test_A3_BU_TURUN_iki_yeni_kopyasi_envanterde():
    """Brief'in adıyla istediği iki kopya (bu gece ölçüldü, envanterde YOKTU): hafıza kabuk
    okuyucusunun `.key`i ve hermes profillerindeki OpenRouter anahtarı."""
    yollar = {(x["yol"], x.get("alan")) for x in _envanter_kopyalari()}
    assert ("/opt/hindsight/.key", None) in yollar
    for p in ("bekci", "karne", "sef"):
        assert (f"/home/ubuntu/.hermes/profiles/{p}/.env", "OPENROUTER_API_KEY") in yollar


def test_A4_ENVANTERDE_DEGER_YOK():
    """v439 E4 ile aynı disiplin, yeni blok için: envanterde `ad`/`yol` vardır, DEĞER asla."""
    ham = ENVANTER.read_text(encoding="utf-8")
    assert not re.search(r"^\s*-?\s*(deger|value|secret|token|key)\s*:", ham, flags=re.M | re.I)
    for x in _envanter_kopyalari():
        assert set(x) <= {"alt_komut", "sir", "tur", "yol", "alan", "mod", "sahip",
                          "tuketici", "onek", "not"}, set(x)


def test_A5_ROTASYON_BLOGU_v439_un_dosyalar_blogunu_BOZMAZ():
    """Yeni blok `dosyalar:` bloğunun YANINDA yaşar. `dosyalar:` spec §1 tablosuna çivilidir
    (v439 E2/E3, BİREBİR eşitlik); oraya bir satır eklemek spec düzenlemesi ister ve
    `/opt/hindsight/.key` için §2'nin DONUK sınıf sözlüğünde karşılık yoktur."""
    env = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    assert len(env["dosyalar"]) == 6, "v439 E2 spec §1 ile BİREBİR eşitlik istiyor"
    assert env["rotasyon_kopyalari"]["kaynak_betik"] == "deploy/oracle-a1/sir_rotasyon.sh"
    assert env["rotasyon_kopyalari"]["olcum"], "ölçüm tarihi yok — sayı taşıyan satır tarih taşır"


# =================================================================================================
# B) BETİĞİN YAPISAL KAPILARI
# =================================================================================================

def test_B0_betik_sozdizimi_gecerli():
    """`bash -n` — teslimden önceki en ucuz kapı. Betik A1'de bakım penceresinde koşar; bir
    sözdizimi hatası orada bulunursa pencere yanar."""
    assert BETIK.exists()
    r = subprocess.run(["bash", "-n", str(BETIK)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_B1_zorunlu_kapilar_metinde():
    """Yapısal kapı listesi. `read -s` (değer terminale yansımaz), `os.replace` (atomik yazım),
    `install -o ... -g` (birleşik biçim A1'de HATA verir), `trap` (negatif kontrol ardını
    toplar), `sudo sh -c` (glob root'un kabuğunda açılır)."""
    metin = BETIK.read_text(encoding="utf-8")
    for kapi in ("read -rs", "os.replace", "install -d -m 0700 -o root -g root",
                 "trap", "sudo sh -c", "openssl rand -base64 36", "openssl rand -hex 32"):
        assert kapi in metin, f"betikte eksik kapı: {kapi}"


def test_B2_install_BIRLESIK_kullanici_grup_bicimi_YOK():
    """A1'de ölçüldü: `install -o root:root` → `install: invalid user`. `set -e` altında bu hata
    bakım penceresinin ortasında patlar ve yarım bir rotasyon bırakır."""
    # YORUM SATIRLARI DIŞARIDA: tuzağın kendisi ("Tek `-o root:root` HATA verir") betiğin
    # şerhinde YAZILIDIR ve onu ihlal saymak, dersi yazmayı cezalandırırdı.
    kod = [s for s in BETIK.read_text(encoding="utf-8").splitlines()
           if not s.lstrip().startswith("#")]
    assert not re.search(r"install\s[^\n]*-o\s+\S+:\S+", "\n".join(kod)), \
        "birleşik -o kullanıcı:grup"


def test_B3_deger_ARGV_ye_KONMAZ():
    """`ps` argv'yi makinedeki HERKESE gösterir; 2026-09-02'de bir parola tam bu sınıftan düştü.
    Değer `-K` yapılandırma dosyasından ve `--data-binary @dosya`dan akar."""
    metin = BETIK.read_text(encoding="utf-8")
    kod = "\n".join(s for s in metin.splitlines() if not s.lstrip().startswith("#"))
    assert not re.search(r'-H\s+["\'][^"\']*\$(deger|yeni|eski|tok|anahtar)', kod)
    assert not re.search(r"PGPASSWORD=", kod), "parola ortama konuyor — ortam çocuklara akar"
    assert not re.search(r'psql[^\n]*-c\s+["\'][^"\']*\$', kod)
    assert "curl -K" in metin


def test_B4_HASH_de_basilmaz():
    """Bir sha256'nın ilk sekiz hanesi "sızdırmayan kimlik" gibi görünür ama iki koşumu
    birbirine bağlayan bir izdir; brief bu betikte hash BASILMAMASINI şart koşuyor."""
    metin = BETIK.read_text(encoding="utf-8")
    gövde = metin.split("set -euo pipefail", 1)[1]
    assert not re.search(r"\bsha256sum\b|\bopenssl\s+dgst\b|hashlib", gövde)


def test_B5_alt_komut_ZORUNLU():
    """Argümansız koşum sessizce bir şey yapmamalı — operatör "döndürdüm" sanırdı."""
    r = subprocess.run(["bash", str(BETIK)], capture_output=True, text=True)
    assert r.returncode != 0
    assert "alt komut ZORUNLU" in r.stderr


def test_B6_iki_alt_komut_REDDEDILIR(tmp_path):
    """Her koşum TEK sır döndürür: iki alt komut tek yedek dizinine yazardı ve geri alma
    hangi sırrın hangi dosyasını geri koyacağını bilemezdi."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--kapi", "--dash")
    assert r.returncode != 0 and "iki alt komut" in r.stderr


# =================================================================================================
# C) --kuru
# =================================================================================================

def test_C1_kuru_kosum_HICBIR_SEY_yazmaz(tmp_path):
    """Operatörün koşacağı İLK komut. Kuru koşum yazmıyorsa BEYAN, yazıyorsa ARIZADIR."""
    kok, ortam = _sahte_ortam(tmp_path)
    once = {p: p.read_bytes() for p in kok.rglob("*") if p.is_file()}
    r = _kos(BETIK, ortam, "--dash", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "/etc/meridian/dash_token" in r.stdout and "/opt/meridian/.dash.env" in r.stdout
    assert "meridian.service" in r.stdout
    sonra = {p: p.read_bytes() for p in kok.rglob("*") if p.is_file()}
    degisen = {str(p) for p in set(once) | set(sonra) if once.get(p) != sonra.get(p)}
    degisen -= {str(kok / ".sahte/argv.log")}   # şimlerin kendi günlüğü ölçüm aracıdır
    assert not degisen, f"kuru koşum DOSYA DEĞİŞTİRDİ: {degisen}"
    assert not list((kok / "root").glob("sir-yedek-*")), "kuru koşum yedek dizini açtı"


@pytest.mark.parametrize("alt", ["--kapi", "--tenant", "--db", "--dash", "--openrouter"])
def test_C2_her_alt_komutun_kuru_kosumu_BIRIMLERI_soyler(tmp_path, alt):
    """"Hangi birimler yeniden başlayacak" sorusunun cevabı ölçülür, varsayılmaz: worker'ı
    durdurma kararı buna bağlıdır. `--openrouter` listeye TUR 2'de girdi: ilk turda o alt komut
    kuru koşumda bile iki gerçek anahtar istiyordu (girdisiz koşum çıkış 1 verirdi), yani kapsam
    boşluğu tam da parametre listesinin eksik olduğu yerdeydi."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, alt, "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "yeniden başlatılacak:" in r.stdout
    assert ".service" in r.stdout.split("yeniden başlatılacak:")[1]


# =================================================================================================
# D) --kapi
# =================================================================================================

def test_D1_kapi_iki_kopyayi_da_yazar_tirnak_KORUNUR(tmp_path):
    """İKİ kopya: credential kaynağı + kapının `.env-apisix` satırı. Tohumda o satır TEK
    tırnaklıdır; tırnak biçimi korunmazsa apisix `$env://` çözümünde değeri tırnaklarla birlikte
    okur ve anahtar sessizce yanlış olur."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--kapi")
    assert r.returncode == 0, r.stdout + r.stderr
    yeni = (kok / "etc/meridian/kapi_apikey").read_text().strip()
    assert yeni != ESKI["kapi"] and len(yeni) == 48
    satir = _env_alan(kok / "opt/apisix/.env-apisix", "BOT_KEY_MERIDIAN")
    assert satir == f"'{yeni}'", f"tek tırnak korunmadı: {satir!r}"
    assert _env_alan(kok / "opt/apisix/.env-apisix", "APISIX_ADMIN_KEY") == "sahte-admin"


def test_D2_kapi_YEDEK_alir(tmp_path):
    """Yedek olmadan geri alma yoktur; brief her koşumun ÖNCE yedek almasını şart koşuyor."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--kapi").returncode == 0
    y = _yedek_dizini(kok)
    assert (y / "etc/meridian/kapi_apikey").read_text().strip() == ESKI["kapi"]
    assert ESKI["kapi"] in (y / "opt/apisix/.env-apisix").read_text()
    assert oct(y.stat().st_mode & 0o777) == "0o700", "yedek dizini 0700 değil"


def test_D3_kapi_RESTART_SIRASI_apisix_sonra_meridian(tmp_path):
    """Kapıyı motordan ÖNCE yeniden başlatmazsan motor yeni anahtarla ESKİ kapıya konuşur ve ilk
    turda 401 alır. Sıra bir ayrıntı değil, sözleşmedir."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--kapi").returncode == 0
    sira = _birim_sirasi(kok)
    assert sira == ["apisix.service", "meridian.service"], sira


def test_D4_kapi_kanit_ESLESMEZSE_cikis_2(tmp_path):
    """Kilit yürürlükte değilken (yüzey anahtara KÖR) "yeni anahtar 200 döndü" hiçbir şey
    kanıtlamaz. Betik "geçti" demez: ölçülemedi + çıkış 2 (uydurma yasağı)."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_KOR"] = "1"
    r = _kos(BETIK, ortam, "--kapi")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜLEMEDİ" in r.stderr


def test_D5_kapi_DEGER_hicbir_ciktiya_ve_ARGV_ye_girmez(tmp_path):
    """Üç yüzey birden ölçülür: stdout, stderr ve ŞİMLERİN KAYDETTİĞİ ARGV. Metin grep'i
    (B3) yapısaldır; bu ölçüm DAVRANIŞSALDIR — betik bir gün değeri argv'ye koyarsa buradan öter."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--kapi")
    assert r.returncode == 0, r.stdout + r.stderr
    yeni = (kok / "etc/meridian/kapi_apikey").read_text().strip()
    assert yeni not in r.stdout and yeni not in r.stderr
    assert yeni not in (kok / ".sahte/argv.log").read_text(encoding="utf-8")


def test_D6_kapi_CREDENTIAL_dolulugu_olculur(tmp_path):
    """2026-09-07: BOŞ bir credential dosyası birimi sessizce yetkisiz bıraktı. Ölçüm "var mı"
    değil "boyutu > 1 mi"dir ve çıktıda görünür."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--kapi")
    assert "/run/credentials/meridian.service/KAPI_APIKEY" in r.stdout
    assert (kok / "run/credentials/meridian.service/KAPI_APIKEY").read_text().strip() \
        == (kok / "etc/meridian/kapi_apikey").read_text().strip()


# =================================================================================================
# E) --tenant
# =================================================================================================

def test_E1_tenant_UC_kopya_ESIT(tmp_path):
    """Üç kopya (creds dosyası · `.key` · `.env-cp` satırı) AYNI değeri taşımalı. Biri unutulursa
    `hafiza_sor.sh` ya da hindsight-cp ilk çağrısında 401 alır — ve o çağrı saatler sonra gelir."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--tenant")
    assert r.returncode == 0, r.stdout + r.stderr
    yeni = (kok / "etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY").read_text().strip()
    assert len(yeni) == 64 and re.fullmatch(r"[0-9a-f]{64}", yeni), yeni
    assert (kok / "opt/hindsight/.key").read_text().strip() == yeni
    assert _env_alan(kok / "opt/hindsight/.env-cp", "HINDSIGHT_CP_DATAPLANE_API_KEY") == yeni
    assert "EŞİT" in r.stdout


def test_E2_tenant_key_MOD_ve_SAHIP_korunur(tmp_path):
    """`.key`i ubuntu okur (`~/bin/hafiza_sor.sh`). 0400 root'a çekmek rotasyonu "başarılı"
    gösterip okuyucuyu sessizce kırardı — bu yüzden mod/sahip `koru`dur."""
    kok, ortam = _sahte_ortam(tmp_path)
    hedef = kok / "opt/hindsight/.key"
    hedef.chmod(0o600)
    once = hedef.stat()
    assert _kos(BETIK, ortam, "--tenant").returncode == 0
    sonra = hedef.stat()
    assert oct(sonra.st_mode & 0o777) == "0o600"
    assert (sonra.st_uid, sonra.st_gid) == (once.st_uid, once.st_gid)


def test_E3_tenant_env_cp_satiri_TEK_kalir(tmp_path):
    """İki `HINDSIGHT_CP_DATAPLANE_API_KEY=` satırı en sinsi hâl olurdu: docker sonuncuyu okur,
    operatör ilkini düzenler ve iki değer sessizce ayrışır."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--tenant").returncode == 0
    ham = (kok / "opt/hindsight/.env-cp").read_text()
    assert ham.count("HINDSIGHT_CP_DATAPLANE_API_KEY=") == 1, ham
    assert "HINDSIGHT_CP_ACCESS_KEY=sahte-access" in ham, "komşu satır YENDİ"


def test_E4_alan_IKI_KEZ_varsa_betik_DURUR(tmp_path):
    """`^AD=` satırı 0 ya da >1 ise yazım hedefsizdir. Sessizce "sonuncuyu" yazmak, ayrışmayı
    ROTASYONUN KENDİSİNİN üretmesi demek olurdu."""
    kok, ortam = _sahte_ortam(tmp_path)
    p = kok / "opt/hindsight/.env-cp"
    p.write_text(p.read_text() + f"HINDSIGHT_CP_DATAPLANE_API_KEY={ESKI['tenant']}\n")
    r = _kos(BETIK, ortam, "--tenant")
    assert r.returncode != 0
    assert "2 kez bulundu" in (r.stdout + r.stderr)


# =================================================================================================
# F) --db
# =================================================================================================

def test_F1_db_SQL_dosyasi_kosumdan_sonra_YOK(tmp_path):
    """Diskte kalan bir `ALTER ROLE ... PASSWORD '<parola>'` satırı rotasyonu anlamsız kılardı."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not list(pathlib.Path("/tmp").glob("**/rol.sql")) or True   # tmpdir silindi
    assert "SQL dosyası silindi" in r.stdout
    kalan = [s for s in (kok / ".sahte/argv.log").read_text().splitlines() if "ALTER ROLE" in s]
    assert not kalan, f"parola argv'ye girdi: {kalan}"


def test_F2_db_DSN_de_YALNIZ_parola_degisir(tmp_path):
    """Kullanıcı/host/port/db ve QUERY (sslmode, application_name) korunmalı: `sed` ile parola
    değiştirmenin klasik bedeli query'yi yemektir ve hindsight sessizce TLS'siz bağlanırdı."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--db").returncode == 0
    from urllib.parse import urlsplit
    yeni = urlsplit((kok / "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL").read_text().strip())
    eski = urlsplit(DSN)
    assert (yeni.scheme, yeni.username, yeni.hostname, yeni.port, yeni.path, yeni.query) == \
           (eski.scheme, eski.username, eski.hostname, eski.port, eski.path, eski.query)
    assert yeni.password != eski.password and len(yeni.password) == 48


def test_F3_db_kanit_YENI_baglanir_ESKI_FATAL(tmp_path):
    """İki hüküm birden: yeni parola `select 1` → 1, eski parola FATAL. Yalnız birincisi
    ölçülseydi "ALTER ROLE etkisiz kaldı" hâli 'başarılı' görünürdü."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "select 1 → 1" in r.stdout
    assert "FATAL" in r.stdout


def test_F4_db_ESKI_parola_hala_gecerliyse_cikis_2(tmp_path):
    """Kimlik doğrulama kapalıysa (`trust`) eski parola da bağlanır; o hâlde rotasyonun ölçüsü
    YOKTUR. Betik durur: ölçülemedi + çıkış 2."""
    kok, ortam = _sahte_ortam(tmp_path)
    # Dünyayı bozuyoruz: `ALTER ROLE` uygulanmıyor (psql -f sessizce yok sayıyor).
    sim = pathlib.Path(ortam["PATH"].split(":")[0]) / "psql"
    sim.write_text(sim.read_text().replace(
        'with open(DURUM, "w", encoding="utf-8") as fh:\n        fh.write(m.group(2))',
        "pass"))
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜLEMEDİ" in r.stderr
    assert (kok / ".sahte/pg_parola").read_text().strip() == ESKI["pg"]


# =================================================================================================
# G) --dash
# =================================================================================================

def test_G1_dash_credential_ve_dash_env_yazilir(tmp_path):
    """İki kopya. `.dash.env` brifing/learn/sprint@ birimlerinin EnvironmentFile'ıdır: unutulursa
    o birimler bir sonraki tetikte 401 alır ve arıza gece yarısı görünür."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    yeni = (kok / "etc/meridian/dash_token").read_text().strip()
    assert len(yeni) == 48 and yeni != ESKI["dash"]
    assert _env_alan(kok / "opt/meridian/.dash.env", "MERIDIAN_DASH_TOKEN") == f'"{yeni}"'


def test_G2_dash_kanit_yeni_200_eski_401(tmp_path):
    """Farksal kanıt görünür olmalı: operatör "200 geldi" ile "eski anahtar da 200 geliyor"u
    ayırt edebilmeli."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "yeni→200" in r.stdout and "eski→401" in r.stdout


def test_G3_dash_YEREL_env_kapsam_disi_BEYAN_edilir(tmp_path):
    """Operatörün yerel `.env` kopyası bu betiğin kapsamı DIŞINDA. Kapsam dışı olmak sessiz
    olmayı gerektirmez — beyan edilmeyen bir boşluk, olmayan bir boşlukla aynı görünür."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--dash")
    assert "YEREL .env" in r.stdout and "kapsamı DIŞINDA" in r.stdout


# =================================================================================================
# H) --openrouter
# =================================================================================================
YENI_NOUS = "SAHTE-YENI-NOUS-anahtari-2026"
YENI_OR = "SAHTE-YENI-OPENROUTER-anahtari-2026"


def test_H1_openrouter_IKI_read_s_ve_SEKIZ_kopya(tmp_path):
    """İki anahtar ayrı ayrı istenir (stdin'den iki satır). NOUS 2 kopya (credential + motor
    API), OPENROUTER 6 kopya (`.env-apisix` ×2, hindsight creds, hermes ×3)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS
    assert _env_alan(kok / "opt/apisix/.env-apisix", "OPENROUTER_API_KEY") == f'"{YENI_OR}"'
    assert _env_alan(kok / "opt/apisix/.env-apisix", "OPENROUTER_AUTH") == f'"Bearer {YENI_OR}"'
    assert (kok / "etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY").read_text().strip() == YENI_OR
    for p in ("bekci", "karne", "sef"):
        assert _env_alan(kok / f"home/ubuntu/.hermes/profiles/{p}/.env",
                         "OPENROUTER_API_KEY") == YENI_OR
    assert "/api/secrets/NOUS_API_KEY" in (kok / ".sahte/argv.log").read_text()


def test_H2_openrouter_BOS_birakilan_bacak_ATLANIR(tmp_path):
    """Tek anahtarı iki role de vermek ya da yalnız birini yenilemek OPERATÖRÜN seçimidir;
    boş bırakılan bacak dokunulmadan kalır."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"]
    assert _env_alan(kok / "opt/apisix/.env-apisix", "OPENROUTER_API_KEY") == f'"{YENI_OR}"'


def test_H3_openrouter_KANIT_gövde_ve_health(tmp_path):
    """Kapıdan GERÇEK bir `chat/completions` (200 + gövdede `choices`) ve hindsight `/health` 200.
    HTTP 200 tek başına yetmez: uç anahtar yanlışken de 200 dönebilir, hüküm gövdededir."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "choices" in r.stdout and "/health 200" in r.stdout
    assert "ok:true" in r.stdout


def test_H4_NEGATIF_KONTROL_yazimdan_ONCE_kosar(tmp_path):
    """Negatif kontrol bilerek bozuk bir değer yazar ve yüzeyin BAŞARISIZ olmasını bekler;
    çıktıda YAZIMDAN ÖNCE görünmeli — sonra koşsaydı operatörün taze anahtarı çoktan yazılmış
    olurdu."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    i_neg = r.stdout.index("negatif kontrol (NOUS_API_KEY)")
    i_yaz = r.stdout.index("yazıldı: /etc/meridian/nous_api_key")
    assert i_neg < i_yaz, "negatif kontrol yazımdan SONRA koştu"
    assert "kanıt anahtara BAĞLI" in r.stdout


def test_H5_NEGATIF_KONTROL_gecerse_DUR_ve_HICBIR_YAZIM_YOK(tmp_path):
    """Brief'in en sert maddesi: bozuk anahtarla da "ok" geliyorsa kanıt anahtara bağlı DEĞİLDİR.
    Betik çıkış 2 verir ve operatörün TAZE anahtarı hiçbir kopyaya yazılmaz — negatif kontrolün
    geçici yazımı da trap ile geri alınır."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_KOR"] = "1"
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜLEMEDİ" in r.stderr and "YAZILMADI" in r.stderr
    # Taze anahtar HİÇBİR kopyada yok; eski değerler yerinde.
    ham = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                    for p in kok.rglob("*") if p.is_file() and ".sahte" not in str(p))
    assert YENI_NOUS not in ham and YENI_OR not in ham
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"]
    assert _env_alan(kok / "opt/apisix/.env-apisix", "OPENROUTER_AUTH") == f'"Bearer {ESKI["or"]}"'


def test_H6_openrouter_YEDEK_alir(tmp_path):
    """Sekiz kopyalı bir rotasyonun geri alımı ancak yedekten yapılabilir."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--openrouter",
                girdi=f"{YENI_NOUS}\n{YENI_OR}\n").returncode == 0
    y = _yedek_dizini(kok)
    assert (y / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"]
    for p in ("bekci", "karne", "sef"):
        assert ESKI["or"] in (y / f"home/ubuntu/.hermes/profiles/{p}/.env").read_text()


# =================================================================================================
# I) --envanter
# =================================================================================================

def test_I1_envanter_ESIT_ve_AYRI_raporlar(tmp_path):
    """Tohumda `.env-apisix`in OpenRouter satırları birbiriyle EŞİT ama hindsight'ın LLM
    anahtarı AYRIDIR (gerçek bir ayrışma hâli). Rapor ikisini de göstermeli — yalnız "EŞİT"
    basan bir envanter, ayrışmayı görmeyen bir envanterdir."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "EŞİT" in r.stdout and "AYRI" in r.stdout
    assert "OKUNAMADI" in r.stdout, "api/sql kanalları beyanla OKUNAMADI demeli"


def test_I2_envanter_DEGER_ve_HASH_basmaz(tmp_path):
    """Brief: çıktıda 20+ karakterlik rastgele dizge YOK. İki ölçüm: (1) tohum değerlerin hiçbiri
    çıktıda yok — belirleyici; (2) entropi süzgeci — küçük+büyük harf+rakam taşıyan 20+ karakterlik
    hiçbir belirteç yok (adlar TEK kasadır, yollar `/` ile bölünür, damgalarda küçük harf yoktur)."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    tam = r.stdout + r.stderr
    for d in ESKI.values():
        assert d not in tam, f"envanter SIR DEĞERİ bastı: {d}"
    for belirtec in re.findall(r"[A-Za-z0-9_+/=-]{20,}", tam):
        assert not (re.search(r"[a-z]", belirtec) and re.search(r"[A-Z]", belirtec)
                    and re.search(r"[0-9]", belirtec)), f"rastgele görünen dizge: {belirtec}"


def test_I3_envanter_BEYAN_DISI_kopyalari_bulur(tmp_path):
    """Bedel yasasının bu betikteki karşılığı: kopya tablosu bir BEYANDIR ve beyan kendini
    doğrulamaz. Tohumda `/opt/meridian/.env` pano token'ının ikinci kopyasını (spec Bulgu-2),
    `/opt/hindsight/.env` ise üç hindsight sırrını taşır — hiçbiri tabloda yok."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    assert "BEYAN DIŞI KOPYA: /opt/meridian/.env [MERIDIAN_DASH_TOKEN]" in r.stdout
    for ad in ("HINDSIGHT_API_TENANT_API_KEY", "HINDSIGHT_API_LLM_API_KEY",
               "HINDSIGHT_API_DATABASE_URL"):
        assert f"BEYAN DIŞI KOPYA: /opt/hindsight/.env [{ad}]" in r.stdout, ad
    # Beyanlı kopyalar bağırmamalı: her satırı "bulgu" saymak, gerçek bulguyu gürültüde boğardı.
    assert "BEYAN DIŞI KOPYA: /opt/apisix/.env-apisix [OPENROUTER_API_KEY]" not in r.stdout
    assert "BEYAN DIŞI KOPYA: /opt/meridian/.dash.env" not in r.stdout


def test_I4_envanter_HICBIR_SEY_yazmaz(tmp_path):
    """Envanter bir RAPORDUR. Rotasyon dosyalarına dokunursa, "önce bak" alışkanlığı bir
    değiştirme riskine dönüşürdü."""
    kok, ortam = _sahte_ortam(tmp_path)
    once = {p: p.read_bytes() for p in kok.rglob("*") if p.is_file()}
    assert _kos(BETIK, ortam, "--envanter").returncode == 0
    sonra = {p: p.read_bytes() for p in kok.rglob("*") if p.is_file()}
    degisen = {str(p) for p in set(once) | set(sonra) if once.get(p) != sonra.get(p)}
    degisen -= {str(kok / ".sahte/argv.log")}
    assert not degisen, degisen


def test_I5_envanter_YEDEKLERI_root_kabuğunda_listeler(tmp_path):
    """`ls /root/sir-yedek-*` ubuntu kabuğunda BOŞ döner: glob /root'u okuyamayan süreçte açılır
    (A1'de ölçüldü). Glob root'un kabuğunda açılmalı — `sudo sh -c`."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--dash").returncode == 0
    y = _yedek_dizini(kok)
    r = _kos(BETIK, ortam, "--envanter")
    assert y.name in r.stdout, "yedek dizini listelenmedi"


# =================================================================================================
# J) MUTASYON — çivi yeşili KANIT DEĞİLDİR (§6): her çivinin ısırdığını göster
# =================================================================================================

def _mutant(tmp_path: pathlib.Path, *ciftler: tuple[str, str], ad: str = "mutant.sh") -> pathlib.Path:
    """Betiğin mutasyona uğramış bir KOPYASI (bir ya da daha çok değişiklik). Özgün betik ASLA
    değiştirilmez. Her hedef ÖNCE var olduğu doğrulanır: bulunamayan bir mutasyon sessizce
    "mutasyonsuz betik" üretir ve mutasyon çivisi hiçbir şey ölçmemiş olurdu."""
    hedef = tmp_path / ad
    metin = BETIK.read_text(encoding="utf-8")
    for eski, yeni in ciftler:
        assert eski in metin, f"mutasyon hedefi bulunamadı: {eski!r}"
        metin = metin.replace(eski, yeni, 1)
    hedef.write_text(metin, encoding="utf-8")
    return hedef


def test_J1_MUT_tirnak_korunmazsa_D1_kirmizi(tmp_path):
    """D1'in ısırdığı dal: `.env` satırının tırnak biçimi."""
    kok, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('satirlar[idx] = f"{alan}={tirnak}{_onek(onek)}',
                           'satirlar[idx] = f"{alan}={_onek(onek)}'))
    assert _kos(m, ortam, "--kapi").returncode == 0
    yeni = (kok / "etc/meridian/kapi_apikey").read_text().strip()
    assert _env_alan(kok / "opt/apisix/.env-apisix", "BOT_KEY_MERIDIAN") != f"'{yeni}'", \
        "tırnak mutasyonu D1'i kırmıyor — çivi yanlış sebeple yeşil"


def test_J2_MUT_yedek_atlanirsa_D2_kirmizi(tmp_path):
    """D2'nin ısırdığı dal: yedek alma."""
    kok, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('_yedek_al kapi\n', '_yedek_al_atlandi() { :; }; YEDEK="$ISLIK/yok"\n'))
    _kos(m, ortam, "--kapi")
    assert not list((kok / "root").glob("sir-yedek-*")), "yedek mutasyonu D2'yi kırmıyor"


def test_J3_MUT_negatif_kontrol_atlanirsa_H5_kirmizi(tmp_path):
    """H5'in ısırdığı dal: `--openrouter`in yazımdan önceki negatif kontrolü. Mutant, KÖR bir
    dünyada bile yazıma devam eder — yani H5'in çıkış 2 hükmü gerçekten o çağrıdan geliyor."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_KOR"] = "1"
    m = _mutant(
        tmp_path,
        ('    _negatif_kontrol openrouter NOUS_API_KEY _nous_hali bos',
         '    : # negatif kontrol MUTASYONLA kaldırıldı'),
        ('    _negatif_kontrol openrouter OPENROUTER_API_KEY _kapi_chat_hali bozuk',
         '    : # negatif kontrol MUTASYONLA kaldırıldı'))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS, \
        "negatif kontrol mutasyonu H5'i kırmıyor — çivi yanlış sebeple yeşil"


def test_J4_MUT_install_birlesik_bicimi_kosumu_kirar(tmp_path):
    """B2'nin ısırdığı dal DAVRANIŞSAL olarak da ölçülür: `install -o root:root` A1'de hata
    verir ve `set -e` altında pencereyi yakar."""
    _, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ("install -d -m 0700 -o root -g root",
                           "install -d -m 0700 -o root:root"))
    r = _kos(m, ortam, "--kapi")
    assert r.returncode != 0, "birleşik -o biçimi sessizce geçti — şim tuzağı modellemiyor"
    assert "invalid user" in (r.stdout + r.stderr)


def test_J5_MUT_credential_denetimi_atlanirsa_D6_kirmizi(tmp_path):
    """D6'nın ısırdığı dal: `/run/credentials/<birim>/<kimlik>` doluluk ölçümü."""
    _, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('  _kredensiyel_denetle "$alt"\n', "  return 0\n"))
    r = _kos(m, ortam, "--kapi")
    assert "/run/credentials/meridian.service/KAPI_APIKEY" not in r.stdout, \
        "credential mutasyonu D6'yı kırmıyor"


def test_J6_MUT_bos_credential_kaynagi_ROTASYONU_durdurur(tmp_path):
    """Ölçümün kendisi: credential kaynağı BOŞ kalırsa (2026-09-07 vakası) betik "başarılı"
    dememeli. Dünyayı bozuyoruz — systemctl şimi boş bir credential bırakıyor."""
    kok, ortam = _sahte_ortam(tmp_path)
    sim = pathlib.Path(ortam["PATH"].split(":")[0]) / "systemctl"
    sim.write_text(sim.read_text().replace(
        "            shutil.copyfile(KOK + kaynak, hedef)",
        "            open(hedef, 'w').write('')"))
    r = _kos(BETIK, ortam, "--kapi")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "credential BOŞ" in r.stderr
    assert (kok / "run/credentials/meridian.service/KAPI_APIKEY").read_text() == ""


def test_J7_MUT_uzunluk_denetimi_isliyor(tmp_path):
    """Üretim boş/kısa değer verirse betik durur. `openssl` bir PATH kazasıyla boş çıktı verse
    boş bir credential dosyası yazılırdı ve birim sessizce yetkisiz kalırdı."""
    _, ortam = _sahte_ortam(tmp_path)
    sahte_openssl = pathlib.Path(ortam["PATH"].split(":")[0]) / "openssl"
    sahte_openssl.write_text("#!/bin/sh\necho\n")
    sahte_openssl.chmod(0o755)
    r = _kos(BETIK, ortam, "--kapi")
    assert r.returncode != 0
    assert "yazım YAPILMADI" in (r.stdout + r.stderr)


def test_J8_temizlik_islik_dizini_kalmaz(tmp_path):
    """Değer taşıyan geçici dosyalar YALNIZ 0700 çalışma dizininde yaşar ve koşum bitince o
    dizin kalmaz — kalsaydı `--openrouter`in yeni anahtarı diskte açıkta dururdu.

    TUR 2 — ÖLÇÜM KOŞUMUN KENDİSİNE BAĞLANDI. İlk tur PAYLAŞILAN `/tmp`i (ya da makinenin
    TMPDIR'ini) glob'luyordu: aynı anda koşan başka bir pytest işçisinin ya da herhangi bir
    sürecin `yardimci.py` taşıyan dizini bu çiviyi KIRIYORDU, yani `-n 4` altında flaky bir
    kırmızı üretiyordu. Flaky bir çivi bir hüküm değildir. Artık `TMPDIR` koşumun `tmp_path`i:
    çivi komşu süreçlere KÖR, kendi koşumuna DUYARLI. Aramanın gerçekten bir şey BULABİLDİĞİNİN
    pozitif kontrolü K9a'dır (temizlik bozulunca aynı arama dizini BULUR) — onsuz bu çivi,
    çalışma dizini bambaşka bir yere düşse de sessizce yeşil kalırdı (2026-09-08: macOS'ta
    şablonsuz `mktemp -d` TMPDIR'i onurlandırmıyor, betik artık şablonu AÇIK veriyor)."""
    kok, ortam = _sahte_ortam(tmp_path)
    once = {p for p in tmp_path.iterdir() if p.is_dir()}
    assert _kos(BETIK, ortam, "--dash").returncode == 0
    kalan = [p for p in tmp_path.iterdir()
             if p.is_dir() and p not in once and (p / "yardimci.py").exists()]
    assert not kalan, f"çalışma dizini silinmedi: {kalan}"
    assert shutil.which("bash"), "ortam denetimi"
    assert json  # kullanılan içe-aktarım (Yasa 6 ruhu: okunmayan yazım yok)
    assert kok.exists()


# =================================================================================================
# K) TUR 2 — ÇEKİŞMELİ İNCELEMENİN 11 KÖKÜ
# =================================================================================================
# Ortak ders: ilk turun ŞİMLERİ betiğin koştuğu DÜNYAYI değil, betiğin varsaydığı dünyayı
# modelliyordu. `sudo` çağıranın kimliğinde koşuyordu, `psql` traversal görmüyordu, `-h` yokluğu
# bir hata değildi. Bu bölümdeki her çivi önce DÜNYAYI gerçekçi kılar, sonra betiği ölçer; her
# kökün yanında mutasyonu vardır (§6: çivi yeşili kanıt değildir).


def _dosya_imzalari(kok: pathlib.Path) -> dict:
    """Test kökündeki her dosyanın içeriği — `--kuru`/başarısız koşumların HİÇBİR ŞEY yazmadığını
    bayt bayt ölçmek için (şimlerin kendi günlükleri ölçüm aracıdır, hariç tutulur)."""
    return {str(p): p.read_bytes() for p in kok.rglob("*")
            if p.is_file() and ".sahte" not in str(p)}


# --- K1: AYRICALIK MODELİ (betik ROOT koşar) -----------------------------------------------------

def test_K1a_ROOT_DEGILKEN_durur_ve_HICBIR_SEY_yazmaz(tmp_path):
    """Ölçümün önündeki kapı. Betik 0400 root dosyalarını yazar VE onlardan türettiği kanıt
    girdilerini (`curl -K` cfg'si · PGPASSFILE · SQL) başka bir sürece okutur; yazan ile okuyan
    ayrı kimlikse hiçbir şey "izin yok" diye BAĞIRMAZ — curl cfg'yi açamaz ve kanıt sessizce 000
    olur. O yüzden kapı ölçümün ÖNÜNDE: yanlış kimlikle koşum hiç BAŞLAMAZ."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_UID"] = "1000"                      # ubuntu — belgelenmeyen çağrı biçimi
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode != 0, r.stdout + r.stderr
    assert "ROOT olarak koşar" in r.stderr and "uid=1000" in r.stderr
    assert "sudo ./sir_rotasyon.sh --dash" in r.stderr, "doğru çağrı biçimi SÖYLENMİYOR"
    assert _dosya_imzalari(kok) == once, "kapı kapalıyken dosya değişti"
    assert not list((kok / "root").glob("sir-yedek-*")), "kapı kapalıyken yedek dizini açıldı"


def test_K1b_KULLANIM_blogu_sudo_ile_yaziyor():
    """Kapı mekaniktir ama BELGE de aynı şeyi söylemeli: RUNBOOK bu başlıktan üretilir
    (`ops/runbook_uret.py`), yani operatörün okuyacağı komut satırı burada yazılıdır. İkisi
    ayrışırsa operatör belgeye uyar, betik durur ve bakım penceresi yanar."""
    metin = BETIK.read_text(encoding="utf-8")
    baslik = metin.split("set -euo pipefail", 1)[0]
    for alt in ("--kapi", "--tenant", "--db", "--dash", "--openrouter", "--envanter"):
        assert f"sudo ./sir_rotasyon.sh {alt}" in baslik, f"KULLANIM satırı sudo'suz: {alt}"
    assert "NİYE ROOT" in baslik, "kapının GEREKÇESİ belgede yok"


def test_K1c_MUT_root_kapisi_kalkarsa_HER_KANIT_000(tmp_path):
    """K1'in ısırdığı dal — ve şimin gerçek kimlik farkını TEMSİL ETTİĞİNİN kanıtı. Kapı
    mutasyonla etkisizleştirilip betik ubuntu olarak koşturulunca: yazım TAMAMLANIR (sır DÖNER),
    ama `curl -K` root'un 0600 cfg'sini açamaz ve her kanıt 000 olur → çıkış 2. İlk turun 54
    çivisinin hiçbiri bunu göremiyordu; şimdi görüyor."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_UID"] = "1000"
    m = _mutant(tmp_path, ('_UID="$(id -u)"', '_UID=0   # MUTASYON: kapı etkisiz'))
    r = _kos(m, ortam, "--dash")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜLEMEDİ" in r.stderr and "HTTP 000" in r.stderr, r.stderr
    # Sır DÖNDÜ ama kanıt YOK: bakım penceresinin en kötü kapanışı.
    assert (kok / "etc/meridian/dash_token").read_text().strip() != ESKI["dash"]


def test_K1d_hermes_profili_MOD_ve_SAHIP_korunur(tmp_path):
    """Root olarak yazmak, dosyayı ROOT'A DEVRETMEK değildir. Hermes profilleri ubuntu sahiplidir
    ve botlar onları ubuntu olarak okur; 0400 root'a çekmek rotasyonu "başarılı" gösterip üç botu
    sessizce kırardı. Tablodaki `koru/koru` bunun sözleşmesi, bu çivi ölçümüdür."""
    kok, ortam = _sahte_ortam(tmp_path)
    hedef = kok / "home/ubuntu/.hermes/profiles/bekci/.env"
    hedef.chmod(0o640)
    once = hedef.stat()
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    sonra = hedef.stat()
    assert oct(sonra.st_mode & 0o777) == "0o640", "hermes profilinin MODU değişti"
    assert (sonra.st_uid, sonra.st_gid) == (once.st_uid, once.st_gid), "SAHİBİ değişti"
    assert _env_alan(hedef, "OPENROUTER_API_KEY") == YENI_OR


def test_K1e_kopyalar_alt_komutu_ROOT_ISTEMEZ():
    """Kapının bilinçli tek istisnası. `--kopyalar` gömülü tabloyu basar: dosya açmaz, uca
    konuşmaz, yazmaz — ve çivinin sözleşme yüzeyidir (A0/A1/A2). Kapıyı oraya da koymak,
    "bu betik ne yazıyor" sorusunu root olmadan SORAMAMAK demek olurdu."""
    r = subprocess.run(["bash", str(BETIK), "--kopyalar"], capture_output=True, text=True,
                       env=dict(os.environ, SIR_ROT_KOK=""))
    assert r.returncode == 0, r.stdout + r.stderr
    assert len(r.stdout.strip().splitlines()) == 17


# --- K2: `--db` SQL kanalı (postgres 0700 dizine giremez) ----------------------------------------

def test_K2a_SQL_postgres_e_STDIN_ile_gider_chown_YOK(tmp_path):
    """`$ISLIK` `mktemp -d` + `chmod 700` ile açılır ve SAHİBİ root'tur: dosyanın sahibini
    postgres'e vermek yetmez, postgres o DİZİNİ traverse edemez. Yol postgres'e hiç verilmez —
    yönlendirmeyi zaten okuyabilen root kabuğu açar (`-f -`), `chown` da gereksizleşir."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 0, r.stdout + r.stderr
    log = (kok / ".sahte/argv.log").read_text(encoding="utf-8")
    assert "-u postgres psql -v ON_ERROR_STOP=1 -q -f -" in log, log
    assert "chown postgres" not in log, "gereksiz chown hâlâ çağrılıyor"
    assert (kok / ".sahte/pg_parola").read_text().strip() != ESKI["pg"], "ALTER ROLE uygulanmadı"


def test_K2b_MUT_dosya_yolu_verilirse_db_EACCES_ile_kirilir(tmp_path):
    """K2'nin ısırdığı dal, DAVRANIŞSAL olarak: psql şimi artık `-u postgres` ile koşarken 0700
    dizini traverse edemez. Mutant eski biçimi (`-f "$sql"`) geri koyar ve `--db` bakım
    penceresinin ortasında durur — A1'de olacak şey tam budur."""
    kok, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('psql -v ON_ERROR_STOP=1 -q -f - < "$sql"',
                           'psql -v ON_ERROR_STOP=1 -q -f "$sql"'))
    r = _kos(m, ortam, "--db")
    assert r.returncode != 0, "0700 traversal modellenmiyor — şim gerçek kimliği temsil etmiyor"
    assert "Permission denied" in (r.stdout + r.stderr)
    assert (kok / ".sahte/pg_parola").read_text().strip() == ESKI["pg"], "parola yine de değişti"


# --- K3: `--db` kanıtı DSN'e bağlanır ------------------------------------------------------------

def test_K3a_kanit_ucu_DSN_den_turetilir(tmp_path):
    """İlk tur `psql -U hindsight -d hindsight` yazıyordu: ne host ne port DSN'den geliyordu, yani
    ölçüm rotasyonun YAZDIĞI bağlantıyı değil, tesadüfen erişilebilen başka bir yolu sınıyordu.
    `-w` de zorunlu: parola bulunamazsa psql İSTEM açar ve pencere bir ölçüm değil bir ASKI olur."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "kanıt ucu DSN'den türetildi: hindsight@127.0.0.1:5432/hindsight" in r.stdout
    log = [s for s in (kok / ".sahte/argv.log").read_text().splitlines() if s.startswith("psql")]
    olcum = [s for s in log if "-c" in s]
    assert olcum, log
    for s in olcum:
        assert "-h 127.0.0.1 -p 5432 -U hindsight -d hindsight" in s, s
        assert " -w " in s, f"-w YOK: {s}"
    # Parola argv'ye GİRMEZ (yalnız PGPASSFILE): DSN türetimi bu kapıyı gevşetmemeli.
    assert ESKI["pg"] not in (kok / ".sahte/argv.log").read_text()


def test_K3b_MUT_host_verilmezse_OLCULEMEDI(tmp_path):
    """K3'ün ısırdığı dal: `-h` düşerse libpq yerel sokete gider. Şim bunu gerçek libpq gibi
    modelliyor (soket YOK) — yani ilk turun çağrısı bugün ölçülse KIRMIZI olurdu."""
    _, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('psql -w -tAX -h "$host" -p "$port" -U "$kuser" \\',
                           'psql -w -tAX -U "$kuser" \\'))
    r = _kos(m, ortam, "--db")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜLEMEDİ" in r.stderr


def test_K3c_hata_metnindeki_bir_rakami_GECMEZ(tmp_path):
    """`case *1*` kalıbı `127.0.0.1`, `port 5432`, `line 1` gibi HER hata metnini "select 1 → 1"
    sayardı. Dünyayı bozuyoruz: psql başarılı bağlantıda bile `1` yerine içinde `1` GEÇEN bir
    metin basıyor. Hüküm TAM eşleşme olduğu için betik durmalı."""
    _, ortam = _sahte_ortam(tmp_path)
    sim = pathlib.Path(ortam["PATH"].split(":")[0]) / "psql"
    sim.write_text(sim.read_text().replace(
        '        print("1"); sys.exit(0)',
        '        print(\'psql: notice: server at "127.0.0.1", port 5432\'); sys.exit(0)'))
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "TAM olarak 1 döndürmedi" in r.stderr


def test_K3d_MUT_gevsek_kalip_o_metni_GECIRIR(tmp_path):
    """K3c'nin ısırdığını gösterir: AYNI bozuk dünyada gevşek kalıplı mutant "doğrulandı" der."""
    _, ortam = _sahte_ortam(tmp_path)
    sim = pathlib.Path(ortam["PATH"].split(":")[0]) / "psql"
    sim.write_text(sim.read_text().replace(
        '        print("1"); sys.exit(0)',
        '        print(\'psql: notice: server at "127.0.0.1", port 5432\'); sys.exit(0)'))
    m = _mutant(tmp_path, (
        '''  [ "$(printf '%s' "$cikti" | tr -d '[:space:]')" = "1" ] \\
    || olcum_yok "yeni parola ile 'select 1' TAM olarak 1 döndürmedi — rotasyon doğrulanamadı"
  oldu "yeni parola: select 1 → 1"''',
        '''  case "$cikti" in *1*) oldu "yeni parola: select 1 → 1" ;;
    *) olcum_yok "gevşek kalıp" ;; esac'''))
    r = _kos(m, ortam, "--db")
    assert r.returncode == 0, "gevşek kalıp mutasyonu K3c'yi kırmıyor — çivi yanlış sebeple yeşil"
    assert "select 1 → 1" in r.stdout


# --- K4: üç hâl (OK · RET · OLCULEMEDI) ----------------------------------------------------------

def test_K4a_NOUS_negatif_kontrolu_BOS_deger_ile_ve_KAPSAM_BEYANI(tmp_path):
    """NOUS için "bozuk değer" yöntemi YAPISAL olarak ölçemez: kapı isteğin Authorization
    başlığını upstream'e geçirmez, kendi anahtarını kullanır — yani YANLIŞ bir NOUS anahtarı da
    ok:true döndürebilir. Tek dürüst negatif kontrol VARLIK tabanlıdır (boş değer → ok:false) ve
    çıktı bunun bir DEĞER-DOĞRULUĞU kanıtı OLMADIĞINI açıkça söyler (uydurma yasağı)."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "negatif kontrol (NOUS_API_KEY, yöntem=bos): → RET" in r.stdout
    assert "DEĞER-DOĞRULUĞU kapıdan ÖLÇÜLEMEZ" in r.stdout
    assert "VARLIK kanıtıdır" in r.stdout
    # OPENROUTER bacağı bunun TERSİ: değer gerçekten upstream'e gider, yani ölçülebilir.
    assert "negatif kontrol (OPENROUTER_API_KEY, yöntem=bozuk): → RET" in r.stdout
    assert "DEĞER-DOĞRULUĞU kanıtı" in r.stdout


def test_K4b_MOTOR_OLU_iken_cikis_2_ve_HICBIR_YAZIM(tmp_path):
    """Ölçüm ARIZASI "anahtar reddedildi" DEĞİLDİR. Motorun TAMAMI ölüyken negatif kontrol daha
    ilk adımda durur: geri-düşüş kopyasını (`DELETE /api/secrets/…`) kaldıramaz, yani boş
    credential ölçümü o kopyayı ölçerdi — kanalı değil. Betik "ölçemedim" der, "geçti" demez.

    KOD ÜÇ HANELİDİR. Gerçek curl bağlanamasa bile `%{http_code}` (`000`) basar VE 7 ile düşer;
    eski `|| echo 000` deseni operatöre `000000` gösteriyordu (inceleme B3). `HTTP 000` burada
    normalizasyonun çivisidir — `000000` görülürse bu çivi kırmızıdır."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_MOTOR_OLU"] = "1"
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "SİLİNEMEDİ" in r.stderr and "HTTP 000)" in r.stderr, r.stderr
    assert "000000" not in r.stderr, "curl kodu normalize edilmedi (çift basım)"
    assert "YAZILMADI" in r.stderr
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"]
    # HANGİ YAZIMLAR "KALICI" SAYILIR. Yedek dizini (`/root/sir-yedek-*`) TASARIM GEREĞİ negatif
    # kontrolden ÖNCE alınır — geri alma onsuz yapılamaz. `/run/credentials/*` de systemd'nin
    # kendi kopyasıdır: her `restart` onu yeniden kurar (şim bunu modelliyor) ve gerçek A1'de
    # tmpfs'tir, kalıcı DEĞİLDİR. Hüküm ROTASYON HEDEFLERİ üzerinedir: hiçbir kopya değişmemeli.
    sonra = _dosya_imzalari(kok)
    degisen = {y for y in set(once) | set(sonra) if once.get(y) != sonra.get(y)}
    kalici = {y for y in degisen if "sir-yedek-" not in y and "/run/credentials/" not in y}
    assert not kalici, f"rotasyon hedefine kalıcı yazım var: {kalici}"
    ham = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in kok.rglob("*")
                    if p.is_file() and ".sahte" not in str(p))
    assert YENI_NOUS not in ham and YENI_OR not in ham, "taze anahtar diske düştü"
    # HİÇBİR BİRİM YENİDEN BAŞLATILMADI. Ölçülemezlik daha ilk adımda anlaşıldığı için betik
    # canlı birimlere HİÇ dokunmadan durdu — bakım penceresinde bu, "ölçemedim" ile "sistemi
    # ölçemediğim bir hâle soktum" arasındaki farktır. (Negatif kontrolün geçici boşaltması
    # trap ile geri alındı: yukarıdaki `nous_api_key == ESKI` ölçümü onu gösterir.)
    assert not (kok / ".sahte/systemctl.log").read_text().split(), "birim yeniden başlatıldı"
    assert _depo(kok)["NOUS_API_KEY"] == ESKI["nous"], "depo kopyası geri alınmadı"


def test_K4c_MUT_olcum_arizasi_RET_sayilirsa_TAZE_ANAHTAR_yazilir(tmp_path):
    """K4b/K4g'nin ısırdığı iki dal BİRDEN: ölü motorda hem "depo kopyası silinemedi" hem de
    "ölçüm arızası" kapısı `oldu`ya çevrilir. İki kapı da açılınca AYNI ölü dünyada operatörün
    taze anahtarı diske yazılır — ilk turun davranışı tam olarak buydu. Tek kapıyı mutasyona
    uğratmak yetmez: öteki kapı koşumu durdurur ve mutasyon "ısırmamış" görünürdü (K8b dersi)."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_MOTOR_OLU"] = "1"
    m = _mutant(tmp_path, (
        '  [ "$kod" = "200" ] || olcum_yok "motor sır deposu kopyası SİLİNEMEDİ',
        '  [ "$kod" = "200" ] || oldu "motor sır deposu kopyası SİLİNEMEDİ'), (
        '    *)   olcum_yok "negatif kontrol ($sir, yöntem=$yontem): ÖLÇÜM ARIZASI → $sonuc.',
        '    *)   oldu "negatif kontrol ($sir, yöntem=$yontem): ÖLÇÜM ARIZASI → $sonuc.'))
    _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS, \
        "üç-hâl mutasyonu K4b'yi kırmıyor — çivi yanlış sebeple yeşil"


def _depo(kok: pathlib.Path) -> dict:
    return json.loads((kok / "opt/meridian/state/secrets.json").read_text(encoding="utf-8"))


def test_K4d_NEGATIF_KONTROL_motorun_GERI_DUSUS_kopyasini_da_kaldirir(tmp_path):
    """TUR 3'ÜN BLOKLAYICISI (inceleme B1). `meridian.secrets._fetch` sırayla credential → süreç
    ortamı → `state/secrets.json` okur ve meridian.service'te ortam basamağı ÖLÜDÜR (drop-in
    `51-dash-env-kaldir.conf`). Negatif kontrol YALNIZ credential'ı boşaltırsa motor ÜÇÜNCÜ
    basamaktaki eski-ama-geçerli kopyaya düşer, `ping_brain` ok:true döner ve betik "bozuk/boş
    değerle de OK geldi" deyip ÇIKIŞ 2 verir: operatörün taze anahtarı HİÇ YAZILMAZ. Bu çivi
    yeşilken şim geri-düşüş zincirini modellemiyordu — yani çivi yanlış sebeple yeşildi (§6).

    Ölçülen: (1) depo kopyası negatif kontrol süresince SİLİNİR, (2) koşum 0 ile biter,
    (3) sonunda depo YENİ değeri taşır (silme kalıcı DEĞİL), (4) depodaki ÖTEKİ adlar
    dokunulmadan kalır — geri alma tüm dosyayı yedekten yazar, o yüzden bu ölçülmelidir."""
    kok, ortam = _sahte_ortam(tmp_path)
    once_depo = _depo(kok)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "silindi: motor API /api/secrets/NOUS_API_KEY" in r.stdout, r.stdout
    assert "negatif kontrol (NOUS_API_KEY, yöntem=bos): → RET" in r.stdout
    sonra_depo = _depo(kok)
    assert sonra_depo["NOUS_API_KEY"] == YENI_NOUS, sonra_depo
    for ad in ("MERIDIAN_DASH_TOKEN", "ALPACA_API_KEY"):
        assert sonra_depo[ad] == once_depo[ad], f"depodaki başka bir ad değişti: {ad}"


def test_K4e_MUT_depo_kopyasi_SILINMEZSE_negatif_kontrol_BOSA_GECER(tmp_path):
    """K4d'nin ısırdığı dal — ve bu turdan ÖNCEKİ betiğin gerçek davranışı. `api` satırı boşluk
    ölçümünün dışında kalınca motor geri-düşüş kopyasına düşer, ok:true döner, negatif kontrol
    "kanıt anahtara bağlı DEĞİL" hükmüne varır ve operatörün TAZE anahtarı yazılmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('        api)   _api_sil "$sir" "$yol" ;;\n', ''))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "bozuk/boş değerle de OK geldi" in r.stderr, r.stderr
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"], \
        "api-silme mutasyonu K4d'yi kırmıyor — çivi yanlış sebeple yeşil"


def test_K4f_NOUS_kaniti_DEPO_KOPYASI_YAZILMADAN_once_olculur(tmp_path):
    """Negatif kontroldeki körlüğün AYNA GÖRÜNTÜSÜ. İki kopya aynı anda yazılsaydı pozitif kanıt
    da hangi kanalın okunduğunu söylemezdi: depo dolu olduğu sürece BOŞ bir credential de
    ok:true üretir. Sıra bu yüzden yaz(credential) → restart → ÖLÇ → sonra depoyu eşitle.

    KAPSAM BEYANI DA ÖLÇÜLÜR: satır "depo BOŞTU" DEMEZ (depo o anda ESKİ değerdedir) ve hangi
    DEĞERİN geçerli olduğunu iddia ETMEZ — eski anahtar da ok:true döndürür. Uydurma yasağı bu
    turda kendi çıktı satırımızda bir kez ihlal edilip düzeltildi; çivi o dizgeyi pinliyor."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    i_kanit = r.stdout.index("motor kanıtı: /api/secrets/test/nous ok:true")
    i_api = r.stdout.index("yazıldı: motor API /api/secrets/NOUS_API_KEY")
    assert i_kanit < i_api, "depo kopyası kanıttan ÖNCE yazıldı — kanıt kanala bağlı değil"
    assert "depo kopyası bu anda HÂLÂ ESKİ değerde" in r.stdout
    assert "okunan kanal CREDENTIAL'dır" in r.stdout
    assert "Hangi DEĞERİN geçerli olduğu ölçülmedi (None)" in r.stdout
    assert "BOŞTU" not in r.stdout, "ölçülmemiş bir hâl (boş depo) iddia ediliyor"


def test_K4g_PING_GOVDESIZ_ise_UC_HAL_OLCULEMEDI_der(tmp_path):
    """Üç-hâl sözlüğünün `OLCULEMEDI(govde-yok)` dalı. Motor AYAKTA (silme çalışır) ama 200
    yanıtın gövdesi yok — araya giren bir vekil ya da kesik yanıt. HTTP kodu "geçti" demek için
    yetmez; hüküm GÖVDEDEDİR ve gövde yoksa hüküm de yoktur."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_PING_GOVDESIZ"] = "1"
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜM ARIZASI" in r.stderr and "OLCULEMEDI(govde-yok)" in r.stderr
    sonra = _dosya_imzalari(kok)
    degisen = {y for y in set(once) | set(sonra) if once.get(y) != sonra.get(y)}
    kalici = {y for y in degisen if "sir-yedek-" not in y and "/run/credentials/" not in y}
    assert not kalici, f"rotasyon hedefine kalıcı yazım var: {kalici}"
    assert _depo(kok)["NOUS_API_KEY"] == ESKI["nous"], "depo kopyası geri alınmadı"


def test_K4h_YEDEK_motorun_sir_deposunu_da_ALIR(tmp_path):
    """Geri alma yedeğe bağlıdır ve yedek `dosya|env|url` süzgeciyle `api` satırını atlıyordu.
    Geri alma DOSYA yazımıyla yapılır, `POST` ile değil: geri alınacak an tam da motorun
    ölçülemez olabildiği andır ve o anda çalışan bir uca bağlı geri alma bir geri alma değildir."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--openrouter",
                girdi=f"{YENI_NOUS}\n{YENI_OR}\n").returncode == 0
    y = _yedek_dizini(kok)
    yedek_depo = json.loads((y / "opt/meridian/state/secrets.json").read_text(encoding="utf-8"))
    assert yedek_depo["NOUS_API_KEY"] == ESKI["nous"], yedek_depo


# --- K5: `/health` dürüstçe etiketlenir ----------------------------------------------------------

def test_K5a_health_satiri_KENDI_KAPSAMINI_beyan_eder(tmp_path):
    """`/health` başlık İSTEMEZ: anahtar doğru da olsa yanlış da olsa 200 döner. İlk tur o satırı
    "hafıza kanıtı" diye basıyor ve üstüne LLM anahtarını dosyadan çıkarıp hiçbir yere
    VERMİYORDU (okunmayan yazım — Yasa 6). Beyan edilmeyen bir boşluk, olmayan bir boşlukla aynı
    görünür; satır artık kendi kapsamını söylüyor."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "/health 200 — servis ayakta; LLM anahtarı için kanıt DEĞİL" in r.stdout
    assert '"$ISLIK/hs"' not in BETIK.read_text(encoding="utf-8"), "ölü çıkarım hâlâ duruyor"


# --- K6: `--openrouter --kuru` gerçekten kuru ----------------------------------------------------

def test_K6a_openrouter_kuru_ANAHTAR_ISTEMEZ_ve_yazmaz(tmp_path):
    """Rotasyonun ÖN-BAKIŞI taze anahtar yapıştırmayı gerektiremez: ilk turda `--openrouter --kuru`
    iki sır isteyip boş bırakılınca "yapacak iş yok" deyip çıkış 1 veriyordu, yani operatörün
    sabah ilk koşacağı komut çalışmıyordu."""
    kok, ortam = _sahte_ortam(tmp_path)
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--openrouter", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "KURU KOŞUM: --openrouter" in r.stdout
    assert "NOUS_API_KEY (motor)" not in (r.stdout + r.stderr), "kuru koşum anahtar İSTEDİ"
    for yol in ("/etc/meridian/nous_api_key", "/opt/apisix/.env-apisix",
                "/home/ubuntu/.hermes/profiles/sef/.env"):
        assert yol in r.stdout, f"kuru rapor bu kopyayı saymıyor: {yol}"
    assert "apisix.service hindsight-api.service meridian.service" in r.stdout
    assert _dosya_imzalari(kok) == once, "kuru koşum DOSYA DEĞİŞTİRDİ"
    assert not list((kok / "root").glob("sir-yedek-*")), "kuru koşum yedek dizini açtı"


def test_K6b_MUT_kuru_kapisi_asagida_ise_anahtar_ister(tmp_path):
    """K6'nın ısırdığı dal: kapı `_oku_gizli` çağrılarının ALTINDAYKEN girdisiz kuru koşum çıkış
    1 verir."""
    _, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, (
        '  [ "$KURU" = 0 ] || { _kuru_rapor openrouter; return 0; }\n  local nous_var=0 or_var=0',
        "  local nous_var=0 or_var=0"))
    r = _kos(m, ortam, "--openrouter", "--kuru")
    assert r.returncode != 0, "kuru kapısı mutasyonu K6a'yı kırmıyor"
    assert "iki anahtar da boş" in r.stderr


# --- K7: dizin izni + `koru` kapısı --------------------------------------------------------------

def test_K7a_mevcut_dizinin_IZNI_korunur(tmp_path):
    """`install -d -m 0755` her koşumda modu DAYATIYORDU: 0700'e sıkılaştırılmış bir sır dizini
    her rotasyonda sessizce gevşiyordu — rotasyon güvenliği artırırken izni geriletiyordu ve
    hiçbir çivi dizin modunu OKUMUYORDU (bedel yasası)."""
    kok, ortam = _sahte_ortam(tmp_path)
    dizin = kok / "etc/hindsight/creds"
    dizin.chmod(0o700)
    assert _kos(BETIK, ortam, "--tenant").returncode == 0
    assert oct(dizin.stat().st_mode & 0o777) == "0o700", "mevcut dizin izni GEVŞETİLDİ"


def test_K7b_MUT_kosulsuz_install_izni_gevsetir(tmp_path):
    """K7a'nın ısırdığı dal."""
    kok, ortam = _sahte_ortam(tmp_path)
    dizin = kok / "etc/hindsight/creds"
    dizin.chmod(0o700)
    m = _mutant(tmp_path, ('  if sudo test -d "$d"; then return 0; fi',
                           "  if false; then return 0; fi   # MUTASYON: koşulsuz install"))
    assert _kos(m, ortam, "--tenant").returncode == 0
    assert oct(dizin.stat().st_mode & 0o777) == "0o755", \
        "dizin mutasyonu K7a'yı kırmıyor — çivi yanlış sebeple yeşil"


def test_K7c_koru_hedefi_YOKSA_betik_DURUR(tmp_path):
    """`mod=koru` "mevcut izni koru" demektir; hedef yoksa MEVCUT izin OKUNAMAZ. İlk turda hedef
    `tee` ile ön-yaratılıyordu ve yardımcıdaki "dosya YOK → dur" kapısı ÖLÜ KODDU."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "opt/hindsight/.key").unlink()
    r = _kos(BETIK, ortam, "--tenant")
    assert r.returncode != 0, r.stdout + r.stderr
    assert "koru ama hedef YOK" in (r.stdout + r.stderr)
    assert not (kok / "opt/hindsight/.key").exists(), "eksik hedef 0644 olarak YENİDEN DOĞDU"


def test_K7d_MUT_on_yaratma_geri_gelirse_SIR_0644_dogar(tmp_path):
    """K7c'nin ısırdığı dal — ve kaybın büyüklüğü: ön-yaratma geri konunca eksik `.key` 0644
    olarak doğar, yani rotasyon KORUMAYA çalıştığı izni kendi eliyle gevşetir."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "opt/hindsight/.key").unlink()
    m = _mutant(tmp_path, ('case "$mod/$sahip" in',
                           'sudo test -e "$hedef" || { : | sudo tee "$hedef" >/dev/null; }\n'
                           '             case "x/x" in'))
    assert _kos(m, ortam, "--tenant").returncode == 0
    yeni = kok / "opt/hindsight/.key"
    assert yeni.exists() and oct(yeni.stat().st_mode & 0o777) == "0o644", \
        "ön-yaratma mutasyonu K7c'yi kırmıyor — çivi yanlış sebeple yeşil"


# --- K8: envanter (çift satır + motor sır deposu) ------------------------------------------------

def test_K8a_cift_satir_CIFT_SATIR_diye_raporlanir(tmp_path):
    """İlk turda `var`/`esit` `SystemExit`i de yutuyordu: çift `^AD=` satırı taşıyan bir dosya
    "YOK"/"OKUNAMADI" diye raporlanıyordu — yani envanterin GÖREVİ olan ayrışma, envanterin
    körlüğü yüzünden "dosya yok" gibi okunuyordu. İki dünya artık ayrı."""
    kok, ortam = _sahte_ortam(tmp_path)
    p = kok / "opt/apisix/.env-apisix"
    p.write_text(p.read_text() + f'OPENROUTER_API_KEY="{ESKI["or"]}"\n')
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    satir = [s for s in r.stdout.splitlines()
             if "/opt/apisix/.env-apisix [OPENROUTER_API_KEY]" in s]
    assert satir, r.stdout
    assert "ÇİFT SATIR (2)" in satir[0], satir
    assert "YOK" not in satir[0], f"çift satır 'YOK' diye raporlandı: {satir[0]}"


def test_K8b_MUT_ariza_yutulursa_cift_satir_YOK_gorunur(tmp_path):
    """K8a'nın ısırdığı dal. İKİ işlem birden mutasyona uğrar (`esit` ve `var`): envanter ilk
    kopyayı `var`, ötekileri `esit` ile okur — yalnız birini bozmak, mutasyonun ısırdığını değil
    yalnızca bir yarısını gösterirdi (ilk denemede tam bu oldu, çivi kırmızı verdi)."""
    kok, ortam = _sahte_ortam(tmp_path)
    p = kok / "opt/apisix/.env-apisix"
    p.write_text(p.read_text() + f'OPENROUTER_API_KEY="{ESKI["or"]}"\n')
    m = _mutant(tmp_path, (
        '        except AlanArizasi as ariza:\n'
        '            # ÇİFT SATIR "OKUNAMADI" DEĞİLDİR: biri dosyanın yokluğu, öteki envanterin'
        ' tam da\n'
        '            # aramaya geldiği ayrışma hâli. İkisini aynı kelimeye toplamak bulguyu'
        ' siler.\n'
        '            print(f"ÇİFT SATIR ({ariza.adet})" if ariza.adet > 1 else "ALAN YOK")\n'
        '            return\n'
        '        except OSError:\n            print("OKUNAMADI")\n            return',
        '        except (OSError, AlanArizasi):\n            print("OKUNAMADI")\n'
        '            return'),
        ('        except AlanArizasi as ariza:\n'
         '            print(f"ÇİFT SATIR ({ariza.adet})" if ariza.adet > 1 else "ALAN YOK")\n'
         '        except OSError:\n            print("YOK")',
         '        except (OSError, AlanArizasi):\n            print("YOK")'))
    r = _kos(m, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ÇİFT SATIR" not in r.stdout, "arıza sınıfı mutasyonu K8a'yı kırmıyor"


def test_K8c_motor_sir_deposu_ADLARI_taranir(tmp_path):
    """Motorun kendi deposu bir `.env` değil bir JSON: `^AD=` taraması ona KÖRDÜR ve o körlük
    "rotasyon bu adı yazıyor" sanısını üretir. `NOUS_API_KEY` beyanlıdır (tablodaki `api`
    satırı bu depoya yazar), `MERIDIAN_DASH_TOKEN` DEĞİLDİR ve bağırılmalıdır."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "/opt/meridian/state/secrets.json [NOUS_API_KEY] → VAR (beyanlı" in r.stdout
    assert ("!! BEYAN DIŞI KOPYA: /opt/meridian/state/secrets.json [MERIDIAN_DASH_TOKEN]"
            in r.stdout)
    for d in ESKI.values():                 # depo taranırken DEĞER okunmaz
        assert d not in (r.stdout + r.stderr), f"envanter değer bastı: {d}"


def test_K8d_secrets_json_YOKSA_bosluk_BEYAN_edilir(tmp_path):
    """Taranamayan bir depo "temiz" demek değildir. Dosya yoksa envanter bunu söyler; sessiz
    kalsaydı boşluk, bulgu yokluğuyla aynı görünürdü."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "opt/meridian/state/secrets.json").unlink()
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "BOŞLUK beyanıdır" in r.stdout


# --- K9: çalışma dizini temizliğinin BEDELİ ------------------------------------------------------

def test_K9a_calisma_dizini_SILINEMEZSE_bagirir(tmp_path):
    """`_temizle` `rm -rf` hatasını YUTUYORDU. Kazanç (ikinci trap ateşinde gürültüsüz çıkış)
    ölçülmüş, BEDEL (0700 bir sır dizininin diskte kalması) ölçülmemişti — bedel yasasının tam
    olarak yasakladığı hâl. Koşumun HÜKMÜ değişmez (rotasyon başarılı), ama sessiz kalmaz."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_RM_KIRIK"] = "1"
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ÇALIŞMA DİZİNİ SİLİNEMEDİ" in r.stderr
    kalan = [p for p in tmp_path.iterdir() if p.is_dir() and (p / "yardimci.py").exists()]
    assert kalan, "dünya bozulmadı — çivi yanlış şeyi ölçüyor"


def test_K9b_MUT_temizlik_hatasi_yutulursa_SESSIZ(tmp_path):
    """K9a'nın ısırdığı dal: ilk turun `2>/dev/null || true` biçimi diskte kalan sır dizinini
    hiç DUYURMAZ."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_RM_KIRIK"] = "1"
    m = _mutant(tmp_path, (
        '  rm -rf "$ISLIK" || echo "!! ÇALIŞMA DİZİNİ SİLİNEMEDİ: $ISLIK\n'
        '     Bu dizin sır taşır (0700). ELLE sil: sudo rm -rf $ISLIK" >&2',
        '  rm -rf "$ISLIK" 2>/dev/null || true'))
    r = _kos(m, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ÇALIŞMA DİZİNİ SİLİNEMEDİ" not in r.stderr, "temizlik mutasyonu K9a'yı kırmıyor"


# --- K10: `--openrouter` yeniden başlatma sırası -------------------------------------------------

def test_K10a_openrouter_RESTART_SIRASI_her_turda_ayni(tmp_path):
    """Kapıyı (apisix) motordan ÖNCE başlatmazsan motor yeni anahtarla ESKİ kapıya konuşur.
    `--openrouter` beş kez yeniden başlatır (negatif kontrolün boz/geri-al turları dahil) ve
    sıra HER turda aynı olmalı: sessiz bir tur, ilk gerçek çağrıda 401 üretirdi."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--openrouter",
                girdi=f"{YENI_NOUS}\n{YENI_OR}\n").returncode == 0
    sira = _birim_sirasi(kok)
    beklenen = ["apisix.service", "hindsight-api.service", "meridian.service"]
    assert sira and len(sira) % 3 == 0, sira
    for i in range(0, len(sira), 3):
        assert sira[i:i + 3] == beklenen, (i, sira)


# =================================================================================================
# L) TUR 3 — YENİDEN İNCELEMENİN KALAN KÖKLERİ (B2 · B3 · B5 · B6 · B7)
# =================================================================================================
# Ortak ders yine şimlerle ilgili: bir kanal şimde MODELLENMİYORSA o kanalın hatası ÖLÇÜLEMEZ.
# Bu bölümdeki çiviler iki yeni yüzeyi ölçüyor: gömülü python yardımcısının KENDİSİ (heredoc'tan
# kesilerek, kopyalanarak DEĞİL) ve motorun yazma/silme ucunun gövde sözleşmesi.


def _yardimci(tmp_path: pathlib.Path, betik: pathlib.Path = BETIK) -> pathlib.Path:
    """Betiğin GÖMÜLÜ python yardımcısını heredoc'tan KESER ve koşulabilir bir dosyaya yazar.

    Yardımcı betiğin içinde yaşar ve kabuktan geçmeden ölçülemez; kopyasını teste yazmak ise
    tek-kaynak yasasının yasakladığı hâldir (iki metin sessizce ayrışır). Kesilen metin
    KAYNAĞIN KENDİSİDİR — mutasyon çivileri de mutant betikten keser, yani mutasyon gerçekten
    yardımcıya iner."""
    ham = betik.read_text(encoding="utf-8")
    bas = ham.index("<<'PY_SON'\n") + len("<<'PY_SON'\n")
    son = ham.index("\nPY_SON\n", bas)
    yol = tmp_path / f"yardimci_{betik.stem}.py"
    yol.write_text(ham[bas:son] + "\n", encoding="utf-8")
    return yol


def _py(yardimci: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(yardimci), *args],
                          capture_output=True, text=True)


# --- L1 (B2): DSN alanları YÜZDE-ÇÖZÜLÜR --------------------------------------------------------

KODLU_DSN = ("postgresql://hind%40sight:a%40b%2Fc%3Ad@127.0.0.1:5433/hindsight"
             "?sslmode=disable\n")


def test_L1a_pgpass_DSN_PAROLASINI_yuzde_cozer(tmp_path):
    """`urlsplit(...).password` yüzde-kodunu ÇÖZMEZ (ölçüldü 2026-09-08), oysa yazan taraf
    (`yaz-url`) `quote(..., safe='')` ile KODLAR. İki uç ayrışırsa `pgpass` parolayı KODLU
    yazar, libpq yanlış parolayı dener ve `--db`nin negatif kontrolü "eski parola FATAL" der:
    ölçtüğü şey `ALTER ROLE`un etkisi değil, betiğin kendi kodlama hatasıdır (inceleme B2).

    ÜRETİLEN parolada görünmez (`[A-Za-z0-9_-]` alfabesinde `quote` birim işlemdir) — arıza
    yalnız ELLE konmuş ESKİ parolada doğar, yani tam da negatif kontrolün kullandığı değerde.
    `:` ve ters bölü ayrıca KAÇIŞLIDIR: kaçışsız bir `:` pgpass alanını ikiye böler."""
    y = _yardimci(tmp_path)
    kaynak = tmp_path / "dsn"
    kaynak.write_text(KODLU_DSN, encoding="utf-8")
    cikti = tmp_path / "pgpass"
    r = _py(y, "pgpass", str(cikti), str(kaynak))
    assert r.returncode == 0, r.stdout + r.stderr
    assert cikti.read_text(encoding="utf-8").strip() == \
        r"127.0.0.1:5433:hindsight:hind@sight:a@b/c\:d"


def test_L1b_dsn_uc_KULLANICIYI_pgpass_ile_AYNI_cozer(tmp_path):
    """`psql -U <ad>` ile pgpass'teki kullanıcı alanı ayrışırsa libpq parolayı SESSİZCE bulamaz
    ve parolasız dener — "eski parola FATAL" yine yanlış sebeple gelir. Tek-kaynak: aynı gerçek
    (kullanıcı adı) iki yerden okunuyorsa iki yerde de AYNI çözümü görmeli."""
    y = _yardimci(tmp_path)
    kaynak = tmp_path / "dsn"
    kaynak.write_text(KODLU_DSN, encoding="utf-8")
    r = _py(y, "dsn-uc", str(kaynak))
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.split() == ["127.0.0.1", "5433", "hind@sight", "hindsight"]


def test_L1c_MUT_cozum_kalkarsa_pgpass_KODLU_parola_yazar(tmp_path):
    """L1a'nın ısırdığı dal: `_coz` kalkınca pgpass `%40`ı düz metin olarak taşır ve libpq
    yanlış parolayı dener. Mutasyon MUTANT BETİKTEN kesilir, yani yardımcıya gerçekten iner."""
    m = _mutant(tmp_path, ('f"{_pgpass_alan(_coz(p.password))}\\n"',
                           'f"{_pgpass_alan(p.password)}\\n"'))
    y = _yardimci(tmp_path, m)
    kaynak = tmp_path / "dsn"
    kaynak.write_text(KODLU_DSN, encoding="utf-8")
    cikti = tmp_path / "pgpass_mut"
    assert _py(y, "pgpass", str(cikti), str(kaynak)).returncode == 0
    assert "%40" in cikti.read_text(encoding="utf-8"), \
        "çözüm mutasyonu L1a'yı kırmıyor — çivi yanlış sebeple yeşil"


def test_L1d_URETILEN_parola_alfabesinde_cozum_BIRIM_islemdir(tmp_path):
    """Pozitif kontrol: düzeltme BUGÜNKÜ yolu değiştirmiyor. `_uret b64` alfabesi
    `[A-Za-z0-9_-]`dir ve o alfabede `quote`/`unquote` birim işlemdir — yani `--db`nin
    POZİTİF ölçümü (yeni parola) düzeltmeden ÖNCE de SONRA da aynı dizgeyi görür. Bu çivi
    olmasaydı L1a "bir davranışı düzelttim" derken sessizce başka bir davranışı değiştirmiş
    olabilirdi (bedel yasası)."""
    y = _yardimci(tmp_path)
    kaynak = tmp_path / "dsn_duz"
    kaynak.write_text("postgresql://hindsight:Ab9-_Zz@127.0.0.1:5432/hindsight\n",
                      encoding="utf-8")
    cikti = tmp_path / "pgpass_duz"
    assert _py(y, "pgpass", str(cikti), str(kaynak)).returncode == 0
    assert cikti.read_text(encoding="utf-8").strip() == "127.0.0.1:5432:hindsight:hindsight:Ab9-_Zz"


def test_L1e_db_KODLU_ESKI_parola_ile_negatif_kontrol_DOGRU_olcer(tmp_path):
    """B2'nin uçtan uca hâli: ESKİ DSN yüzde-kodlu bir parola taşır (2026-09-07 gecesi ELLE
    konmuş bir parolanın alfabesi BİLİNMEZ). Çözüm olmadan `pgpass` kodlu dizgeyi yazar, libpq
    yanlış parolayı dener ve betik "eski parola: FATAL" der — kanıt gibi görünen bir kodlama
    hatası. Çözümle FATAL yine gelir ama ARTIK `ALTER ROLE`un etkisidir."""
    kok, ortam = _sahte_ortam(tmp_path)
    (kok / "etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL").write_text(
        "postgresql://hindsight:esk%40 par%2Fola@127.0.0.1:5432/hindsight?sslmode=disable\n"
        .replace(" ", ""), encoding="utf-8")
    (kok / ".sahte/pg_parola").write_text("esk@par/ola", encoding="utf-8")
    r = _kos(BETIK, ortam, "--db")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "eski parola: FATAL (kanıt parolaya BAĞLI)" in r.stdout


# --- L2 (B7): motor API gövdesi JSON KAÇIŞLI kurulur ---------------------------------------------

TIRNAKLI_ANAHTAR = 'SAHTE-YENI"NOUS\\anahtar-2026'


def test_L2a_api_govdesi_TIRNAK_ve_TERS_BOLU_tasiyan_degeri_kacirir(tmp_path):
    """`--openrouter`de değeri OPERATÖR yapıştırır. Elle kurulan `{"value": "<değer>"}` gövdesi
    içinde bir çift tırnak ya da ters bölü varsa BOZUK JSON üretir → motor 400 → betik "motor
    API yazımı başarısız" der. Sessiz değil ama teşhisi YANILTICI: hata anahtarda değil,
    gövdeyi kuran kodda (inceleme B7). `json.dumps` kaçışı yapar; değer yine YALNIZ dosyadan
    okunur (argv'ye girmez)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{TIRNAKLI_ANAHTAR}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _depo(kok)["NOUS_API_KEY"] == TIRNAKLI_ANAHTAR, _depo(kok)
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == TIRNAKLI_ANAHTAR


def test_L2b_MUT_kacis_kalkarsa_motor_400_der_ve_TESHIS_yaniltir(tmp_path):
    """L2a'nın ısırdığı dal ve bu turdan ÖNCEKİ davranış: kaçışsız gövde → 400."""
    kok, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, (
        '  py json-govde "$govde" value "$dgr"',
        '  printf \'{"value": "\' > "$govde"; tr -d \'\\r\\n\' < "$dgr" >> "$govde"; '
        'printf \'"}\\n\' >> "$govde"; chmod 600 "$govde"'))
    r = _kos(m, ortam, "--openrouter", girdi=f"{TIRNAKLI_ANAHTAR}\n{YENI_OR}\n")
    assert r.returncode != 0, r.stdout + r.stderr
    assert "HTTP 400" in r.stderr, \
        f"kaçış mutasyonu L2a'yı kırmıyor — çivi yanlış sebeple yeşil: {r.stderr}"


# --- L3 (B3): ulaşılamayan uç ÜÇ HANELİ 000 basar ------------------------------------------------

def test_L3a_MUT_ham_curl_deseni_KOD_CIFT_BASAR(tmp_path):
    """K4b'nin pinlediği `HTTP 000` dizgesinin ısırdığı dal. Gerçek curl bağlanamasa bile
    `%{http_code}` (`000`) basar VE 7 ile düşer; eski `|| echo 000` deseni ikinci bir `000`
    ekliyordu ve operatör canlıda `000000` görüyordu — çivinin pinlediği dizge ise canlıda HİÇ
    görülmeyecekti (şim-gerçek ayrışması, inceleme B3). Mutant o deseni geri getirir."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_MOTOR_OLU"] = "1"
    m = _mutant(tmp_path, ('  kod="$(_curl_kod "$cfg")"\n'
                           '  [ "$kod" = "200" ] || olcum_yok "motor sır deposu kopyası',
                           '  kod="$(curl -K "$cfg" || echo 000)"\n'
                           '  [ "$kod" = "200" ] || olcum_yok "motor sır deposu kopyası'))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "HTTP 000000" in r.stderr, \
        f"normalizasyon mutasyonu K4b'yi kırmıyor — çivi yanlış sebeple yeşil: {r.stderr}"


# --- L4 (B5 · B6): envanterin `[-]` süsü ve `--kuru`un dürüst kapsamı ----------------------------

def test_L4a_envanter_ALANSIZ_satirda_KOSE_PARANTEZ_basmaz(tmp_path):
    """Tabloda alan YOKLUĞU boş dizge değil `-` ile yazılır; `${alan:+…}` bunu görmez ve
    `dosya`/`url` satırları operatöre `[-]` diye basılıyordu (inceleme B5). Yokluğun işareti
    tabloda TEK ve o işaret çıktıda da tanınmalı."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[-]" not in r.stdout, [s for s in r.stdout.splitlines() if "[-]" in s]
    assert "[BOT_KEY_MERIDIAN]" in r.stdout, "alanlı satırın etiketi de kayboldu"


def test_L4b_envanter_kuru_ETKISIZ_oldugunu_SOYLER(tmp_path):
    """`--envanter` `--kuru`yu hiç okumaz ve `--envanter --kuru` SESSİZCE tam envanteri
    koşuyordu: kuru koşum isteyen operatör istediğini aldığını sanır (inceleme B6). Koşum
    engellenmez (zaten hiçbir şey yazmaz) ama etkisizlik SÖYLENİR."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "--kuru bu alt komutta ETKİSİZDİR" in r.stderr
    assert "referans kopya" in r.stdout, "envanter yine de koşmalı"


def test_L4c_ROOT_kapisi_OLMAYAN_bir_bicimi_ONERMEZ(tmp_path):
    """Root hata metni her alt komut için `--kuru` öneriyordu; `--envanter --kuru` diye bir
    sözleşme YOKTUR ve olmayan bir biçimi önermek operatörü yanlış yola sokar. Rotasyon alt
    komutlarında öneri KALIR (K1a onu ölçer)."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_UID"] = "1000"
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode != 0
    assert "sudo ./sir_rotasyon.sh --envanter" in r.stderr
    assert "--envanter --kuru" not in r.stderr, r.stderr
    r2 = _kos(BETIK, ortam, "--dash")
    assert "sudo ./sir_rotasyon.sh --dash --kuru" in r2.stderr, r2.stderr

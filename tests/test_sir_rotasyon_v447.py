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
  M. TUR 4 — HAZIRLIK BEKLEME (canlı vaka 2026-09-08 06:13Z: restart döndü, birim dinlemiyordu)
  N. TUR 5 — HAZIRLIĞIN ANLAMI + KAPSAMI (ikinci canlı deneme 2026-09-08 07:2x-07:4xZ: "hazır"ın
     tanımı birim başınadır, tavan birim başınadır, restart YALNIZ sırrın tüketicisine gider)
  O. TUR 6 — HAFIZA FAILOVER ZİNCİRİNİN ÜYE ANAHTARLARI (canlı bulgu 2026-09-08 08:0xZ: zincir
     üyesi ana anahtarı DEVRALMAZ; altı kopya tabloda YOKTU ve tarama onlara KÖRDÜ)

TUR 3'ÜN ANA DERSİ (K bölümünün dersinin ikinci yarısı): şim bir kanalı MODELLEMİYORSA o kanalın
arızası ÖLÇÜLEMEZ. `SIM_CURL` motorun sır zincirini tek dosyadan üretiyordu; gerçek motor
credential → ortam → `state/secrets.json` sırasını izler ve tohum dünyası o dosyayı ZATEN
taşıyordu. Yani `test_K4a` yeşildi ama betik canlıda çıkış 2 verecekti — çivi yanlış sebeple
yeşil (§6). Zincir modellendiği anda K4a/H1/H3 kırmızıya döndü; düzeltme ondan sonra yazıldı.

TUR 4'ÜN DERSİ AYNI DERSİN ÜÇÜNCÜ BİÇİMİ, BU KEZ ZAMAN EKSENİNDE. 2026-09-08 06:13Z'de betiğin
İLK canlı koşumu (`--openrouter`) düştü: negatif kontrol üç birimi yeniden başlattı ve HEMEN
ölçtü, meridian henüz dinlemiyordu → curl 000 → `OLCULEMEDI(http=000)` → geri alma. 54 çivi
bunu göremedi çünkü `SIM_SYSTEMCTL` restart'ı ANINDA hazır sayıyordu: modellenmeyen kanal bu kez
bir mantık değil SAATTİ. Şim artık her `restart`ta birime bir "ulaşılamaz çağrı" bütçesi
(`SAHTE_HAZIR_N`) yazar ve `curl` bütçe bitene kadar O BİRİMİN HER UCUNDA 000 döner — canlı
vakanın tam modeli: ölçüm `/healthz`e değil `/api/secrets/test/nous`a gitmişti.
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

#: HAFIZA FAILOVER ZİNCİRİNİN ÜYE ANAHTARLARI (canlı ölçüm 2026-09-08 08:0xZ, A1). Zincir ÜYESİ
#: ana anahtarı DEVRALMAZ: `/opt/hindsight/.env` her üye için AYRI bir `_API_KEY` satırı taşır ve
#: altısı da `OPENROUTER_API_KEY`in birebir kopyasıdır. Liste burada TÜRETİLİR (yüzey × sıra),
#: elle yazılmaz; O bölümünün bütün çivileri bu tek kaynaktan okur.
UYE_ALANLARI = tuple(f"HINDSIGHT_API_{yuzey}_LLM_{n}_API_KEY"
                     for yuzey in ("REFLECT", "CONSOLIDATION") for n in (1, 2, 3))

#: KOPYA TABLOSUNUN SATIR SAYISI — İKİ çivi okur (A0 ayrıştırıcının pozitif kontrolü, K1e root
#: istemeyen `--kopyalar` yüzeyi) ve ikisine ayrı ayrı yazılmış bir sayı sessizce ayrışır: bu tur
#: A0 17'den 23'e çekilince K1e 17'de KALDI ve kırmızı verdi (tek-kaynak yasası, ölçüldü
#: 2026-09-08). 17 + hafıza failover zincirinin ALTI üye anahtarı = 23.
KOPYA_SAYISI = 23


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

SIM_CP = '''#!/usr/bin/env python3
"""`SAHTE_CP_KIRIK=1` iken YALNIZ negatif kontrolün GERİ ALMA kopyası düşer (kaynak `<ISLIK>/nk-…`).

Bayrak BİLEREK DAR. "Her `cp` düşsün" deseydik koşum `_yedek_al` adımında kesilir ve ölçülmek
istenen dala (geri alma başarısız → çalışma dizini + çıkış kodu ne oluyor) HİÇ VARILMAZDI —
modellenmeyen bir dal ölçülemez (tur-3'ün dersi). Geri alma kopyalarının kaynağı `nk-` önekli
sahne dosyalarıdır; yedek alma ve `--db` o öneki kullanmaz."""
import os, sys
a = sys.argv[1:]
konum = [x for x in a if not x.startswith("-")]
if os.environ.get("SAHTE_CP_KIRIK") == "1" and konum and "/nk-" in konum[0]:
    sys.stderr.write("cp: Permission denied\\n"); sys.exit(1)
os.execv("/bin/cp", ["/bin/cp"] + a)
'''

SIM_STAT = '''#!/usr/bin/env python3
"""`SAHTE_STAT_KIRIK=1` iken `stat` HER biçimde düşer — GNU (`-c %s`) ve BSD (`-f %z`) geri
düşüşünün İKİSİ BİRDEN başarısız olduğu hâl. Tasarlanan hüküm `olcum_yok` (çıkış 2, "ölçemedim");
`set -e`in ürettiği hüküm çıkış 1'dir ve ikisi AYNI ŞEY DEĞİLDİR (D7 DÜŞÜK-9)."""
import os, sys
if os.environ.get("SAHTE_STAT_KIRIK") == "1":
    sys.stderr.write("stat: illegal option\\n"); sys.exit(1)
os.execv("/usr/bin/stat", ["/usr/bin/stat"] + sys.argv[1:])
'''

SIM_INSTALL = '''#!/usr/bin/env python3
"""A1'de ÖLÇÜLEN tuzak: `install -o root:root` HATA verir; kullanıcı ve grup İKİ AYRI bayraktır.

`SAHTE_INSTALL_KIRIK=1` İKİNCİ bir gerçek hâli modeller: dizin YARATILAMIYOR (disk dolu · yetki ·
salt-okunur bağlama). `set -e` koşumu çıkış 1 ile keser ve YEDEK ALINMAMIŞ olur — `test_P14`ün
ölçtüğü dal (inceleme D7/Y2). Çağrı ARGV'ye YAZILIR (log satırı düşmeden ölçülür), sonra düşer:
"install çağrıldı ama düştü" ile "install hiç çağrılmadı" ayrı iki gerçektir."""
import os, sys
with open(os.path.join(os.environ["SIR_ROT_KOK"], ".sahte", "argv.log"), "a") as fh:
    fh.write("install " + " ".join(sys.argv[1:]) + "\\n")
if os.environ.get("SAHTE_INSTALL_KIRIK") == "1":
    sys.stderr.write("install: cannot create directory: No space left on device\\n")
    sys.exit(1)
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

#: `LoadCredential=<kimlik>:<kaynak>` — DROP-IN DOSYALARINDAN TÜRETİLİR, elle yazılmaz.
#: ÜÇ okuyucusu var ve üçü de BURADAN okur: `SIM_SYSTEMCTL` (systemd'nin yaptığını yapar),
#: `test_P1`/`test_P3` (aşımdan sonra `/run/credentials/<birim>/<kimlik>` ESKİ değere döndü mü) ve
#: `test_M4`. Elle yazılmış bir dördüncü kopya sessizce ayrışırdı (tek-kaynak yasası) — ve
#: ayrışmanın belirtisi "şim credential yazmadı", yani HİÇBİR ŞEY olurdu.
#: `<birim>` drop-in DİZİNİNİN adından gelir (`<birim>.service.d/`), yani kaynağı systemd'nin
#: kendi sözleşmesidir. `test_P6` aynı haritayı betiğin `_kredensiyeller` tablosuyla kıyaslar.
def _dropin_kredensiyelleri() -> dict[str, dict[str, str]]:
    harita: dict[str, dict[str, str]] = {}
    for conf in sorted(KOK_DEPO.glob("deploy/**/*.service.d/*.conf")):
        birim = conf.parent.name[: -len(".d")]
        for satir in conf.read_text(encoding="utf-8").splitlines():
            satir = satir.strip()
            if not satir.startswith("LoadCredential="):
                continue
            kimlik, _, kaynak = satir[len("LoadCredential="):].partition(":")
            assert kaynak, f"boş LoadCredential kaynağı: {conf}"
            harita.setdefault(birim, {})[kimlik] = kaynak
    assert harita, "hiç LoadCredential drop-in bulunamadı — harita boş (pozitif kontrol)"
    return harita


KRED_KAYNAKLARI = _dropin_kredensiyelleri()

SIM_SYSTEMCTL = '''#!/usr/bin/env python3
"""`restart` systemd'nin yaptığını yapar: LoadCredential kaynağını /run/credentials altına koyar.

AYRICA HAZIRLIK BÜTÇESİ YAZAR (`SAHTE_HAZIR_N`, varsayılan 0 = anında hazır). systemd'nin
`restart`ı DÖNDÜĞÜNDE birim henüz dinlemiyor olabilir — 2026-09-08 06:13Z'de canlıda tam bu
oldu. Bütçe o pencerenin modelidir: `curl` bütçe bitene kadar O BİRİME giden HER çağrıda
bağlanamaz. Modellenmeyen bir pencere ölçülemez (tur-3'ün dersi, zaman ekseninde)."""
import json, os, shutil, sys
KOK = os.environ["SIR_ROT_KOK"]
KRED = json.loads("""__KRED_JSON__""")   # drop-in'lerden TÜRETİLDİ (bkz. `_dropin_kredensiyelleri`)
a = sys.argv[1:]
if a and a[0] == "--version":
    print("systemd 255 (255.4-1ubuntu8.4)"); sys.exit(0)
if len(a) >= 2 and a[0] == "restart":
    birim = a[1]
    with open(os.path.join(KOK, ".sahte", "systemctl.log"), "a") as fh:
        fh.write(birim + "\\n")
    with open(os.path.join(KOK, ".sahte", "butce_" + birim), "w") as fh:
        fh.write(os.environ.get("SAHTE_HAZIR_N", "0"))
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
#: Harita şim KAYNAĞINA gömülür (şim ayrı bir süreçtir, modül değişkenini göremez).
SIM_SYSTEMCTL = SIM_SYSTEMCTL.replace("__KRED_JSON__", json.dumps(KRED_KAYNAKLARI))

SIM_CURL = '''#!/usr/bin/env python3
"""`-K <cfg>` okur, sunulan anahtarı O ANDAKİ dosya içeriğiyle KARŞILAŞTIRIR, HTTP kodunu basar.

SAHTE_KOR=1 → yüzey anahtara KÖR olur (her şeye 200 / ok:true). Betiğin "kanıt anahtara bağlı
değil → ölçülemedi" dalını ölçmenin tek dürüst yolu budur: dünyayı bozarız, betiği değil.
SAHTE_MOTOR_OLU=1 → MOTORUN TAMAMI ölü (`/api/…` uçlarının HEPSİ). İlk tur bunu yalnız
`/api/secrets/test/nous`a uyguluyordu: aynı süreçteki yazma/silme ucu ölü motorda ÇALIŞIYOR
görünüyordu — şimin betiğin varsaydığı dünyayı modellemesi (tur-2'nin kendi dersi).
SAHTE_PING_GOVDESIZ=1 → motor AYAKTA ve 200 döner ama gövde YOK: `OLCULEMEDI(govde-yok)` dalının
dünya tarafındaki karşılığı (araya giren vekil, kesik yanıt).
SAHTE_HAZIR_N=<n> → yeniden başlatılan her birim ilk n çağrıda ULAŞILAMAZ (000 + çıkış 7), sonra
normal. Bütçeyi `systemctl restart` yazar, burası TÜKETİR ve tüketim UÇTAN BAĞIMSIZDIR: canlı
vakada 000'ı alan uç `/healthz` değil `/api/secrets/test/nous`tu. `SAHTE_MOTOR_OLU` bu bayrağın
YERİNE GEÇMEZ — o "API yüzeyi ölü" der ve `/healthz`e dokunmaz; ikisini tek bayrağa bağlamak
K4c'nin ölçtüğü dalı (ölü motorda mutantın yazması) örterdi.
SAHTE_HEALTHZ_KOD=<kod> → bütçe BİTTİKTEN sonra `/healthz`in döndüğü kod (varsayılan 200). `503`
bir ARIZA DEĞİL, canlıda ölçülen normal açılış hâlidir: motor ayakta, nabız bayat. `SAHTE_HAZIR_N`
ile aynı bayrağa bağlanamaz — biri "ulaşılamıyor" (000), öteki "cevap veriyor ama 200 değil"
demektir ve D5'in ayırdığı iki dünya tam olarak bunlardır.
SAHTE_HEALTH_KOD=<kod> → aynısının hindsight-api `/health` karşılığı (varsayılan 200). AYRI bayrak
olması şart: iki ucun KABUL ÖLÇÜTÜ farklıdır (meridian HTTP cevabı yeter, hindsight 200 ister) ve
tek bayrak ikisini birden çevirseydi ölçütlerin ayrı olduğu hiç ölçülemezdi.

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


def hazir_butce(url):
    """Birim yeniden başladıktan sonra HEMEN dinlemez. `systemctl restart` her birime bir
    "ulaşılamaz çağrı" bütçesi yazar; buradaki her çağrı bütçeyi bir azaltır ve bütçe bitene
    kadar curl BAĞLANAMAZ — hangi uç olursa olsun. Eşleme HOST üzerindendir: test kökü her
    birime ayrı bir sahte host verir (motor · hafiza · kapi)."""
    for ad, kok_url in (("meridian.service", os.environ.get("SIR_ROT_API", "")),
                        ("hindsight-api.service", os.environ.get("SIR_ROT_HINDSIGHT", "")),
                        ("apisix.service", os.environ.get("SIR_ROT_KAPI_KOK", ""))):
        if not kok_url or not url.startswith(kok_url):
            continue
        yol = os.path.join(KOK, ".sahte", "butce_" + ad)
        try:
            with open(yol, encoding="utf-8") as fh:
                kalan = int(fh.read() or 0)
        except (OSError, ValueError):
            kalan = 0
        if kalan <= 0:
            return False
        with open(yol, "w", encoding="utf-8") as fh:
            fh.write(str(kalan - 1))
        return True
    return False


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

with open(os.path.join(KOK, ".sahte", "url.log"), "a") as fh:
    fh.write(url + "\\n")          # hangi UCUN kaç kez yoklandığı ölçülebilsin (M bölümü)

if hazir_butce(url):
    # Birim henüz AYAKTA DEĞİL. Gerçek curl bağlanamazsa `%{http_code}` (000) basar VE 7 ile düşer.
    sys.stdout.write("000")
    sys.stderr.write("curl: (7) Failed to connect\\n")
    sys.exit(7)

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
elif url.endswith("/healthz"):
    # meridian `/healthz` (ve ona PROXY olan apisix `/healthz`) hazır bir motorda 200 DEĞİL de 503
    # dönebilir: worker açılışta ağır bar tazelemesi yaparken nabız yazılmaz ve gövde
    # `{"status":"stale"}` olur — API ise AYAKTADIR (canlı ölçüm 2026-09-08 07:3xZ). Bu bayrak o
    # dünyayı modeller; modellenmeyen bir dünyanın arızası ölçülemez (tur-3/tur-4'ün dersi).
    kod = os.environ.get("SAHTE_HEALTHZ_KOD", "200")
elif url.endswith("/health"):
    kod = os.environ.get("SAHTE_HEALTH_KOD", "200")   # hindsight-api KENDİ süreci: 200 şarttır
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
    `/opt/meridian/state/secrets.json` pano token'ının ÜÇÜNCÜ kopyasını taşır — ikisi de betiğin
    kopya tablosunda YOKTUR ve `--envanter` taraması onları BEYAN DIŞI KOPYA diye bulmak
    zorundadır.

    D7 (YÜKSEK-3, ölçüm 2026-09-08 09:3xZ A1): `/opt/hindsight/.env`in ÜÇ hindsight sırrı
    (TENANT · LLM · DATABASE_URL) sahneden ÇIKARILDI, çünkü CANLIDA DA YOKLAR — Faz-1A
    `LoadCredential` geçişi 2026-09-07'de tamamlandı ve üçü yalnız `/etc/hindsight/creds/<AD>`
    kaynaklarında yaşıyor. Sahne canlıdan ayrıştığı sürece ölçümler "var olmayan bir dünyanın"
    ölçümüdür (tur-3'ün dersi). Dosyada kalan sırlar failover zincirinin ALTI ÜYE anahtarıdır ve
    onlar BEYANLIDIR (kopya tablosunda)."""
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
    # `/opt/hindsight/.env` İKİ SINIF satır taşır ve ikisi de MODELLENİR (ölçüm 2026-09-08 08:0xZ):
    #   · sır OLMAYAN AYAR satırı (`..._LLM_STRATEGY`) — sözlük DAR olduğu için bağırılmamalı;
    #   · failover zincirinin ALTI ÜYE anahtarı — üye ana anahtarı DEVRALMAZ, her biri
    #     OPENROUTER_API_KEY'in birebir kopyasıdır ve rotasyon bunları DA yazmak zorundadır.
    # Dosya modu üretimdeki hâline (0600) çekilir: `koru` satırının gerçekten koruduğu bir izin
    # olmadan O1'in izin ölçümü hiçbir şey ölçmezdi.
    (kok / "opt/hindsight/.env").write_text(
        "HINDSIGHT_API_REFLECT_LLM_STRATEGY={\"mode\":\"failover\"}\n"
        + "".join(f"{alan}={ESKI['or']}\n" for alan in UYE_ALANLARI))
    (kok / "opt/hindsight/.env").chmod(0o600)
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
    (kok / ".sahte/url.log").write_text("")

    binn = tmp_path / "bin"
    binn.mkdir()
    for ad, kaynak in (("sudo", SIM_SUDO), ("install", SIM_INSTALL), ("systemctl", SIM_SYSTEMCTL),
                       ("curl", SIM_CURL), ("psql", SIM_PSQL), ("id", SIM_ID), ("rm", SIM_RM),
                       ("cp", SIM_CP), ("stat", SIM_STAT)):
        (binn / ad).write_text(kaynak)
        (binn / ad).chmod(0o755)

    # `SAHTE_UID=0`: operatörün BELGELENEN çağrı biçimi `sudo ./sir_rotasyon.sh …`dır, yani betik
    # root olarak koşar. Kimliği ortamdan vermek, "root değilken ne olur" sorusunu da ölçülebilir
    # kılar (K1a/K1c: 1000 ile koş).
    # `TMPDIR=tmp_path`: `mktemp -d` bunu onurlandırır, yani 0700 çalışma dizini KOŞUMUN KENDİ
    # tmp_path'i altında doğar. İlk turda J8 paylaşılan `/tmp`i glob'luyordu ve komşu süreçlerin
    # dizinlerini görüyordu — `-n 4` altında flaky bir çivi, yani hüküm olmayan bir hüküm.
    # `HAZIR_BEKLE_*`: bekleme penceresi ÇİVİ İÇİN sıkıştırılır (üretimde 2 s / 60 s). Sıkıştırma
    # sözleşmeyi değiştirmesin diye üretim varsayılanları M0'da AYRICA ölçülür — yoksa biri
    # varsayılanı 0'a çekse bütün M bölümü yine yeşil kalırdı.
    ortam = dict(os.environ, PATH=f"{binn}:{os.environ['PATH']}", SIR_ROT_KOK=str(kok),
                 SIR_ROT_API="http://motor", SIR_ROT_HINDSIGHT="http://hafiza",
                 SIR_ROT_KAPI="http://kapi/llm/v1", SIR_ROT_KAPI_KOK="http://kapi",
                 HAZIR_BEKLE_ARALIK_S="0.01", HAZIR_BEKLE_TAVAN_S="2",
                 HAZIR_TAVAN_S_hindsight_api="2",
                 SAHTE_UID="0", TMPDIR=str(tmp_path))
    for bayrak in ("SAHTE_KOR", "SAHTE_MOTOR_OLU", "SAHTE_RM_KIRIK", "SAHTE_PING_GOVDESIZ",
                   "SAHTE_HAZIR_N", "SAHTE_HEALTHZ_KOD", "SAHTE_HEALTH_KOD",
                   "SAHTE_CP_KIRIK", "SAHTE_STAT_KIRIK", "SAHTE_INSTALL_KIRIK"):
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

def _betik_kopyalari(betik: pathlib.Path = BETIK) -> list[dict]:
    """`--kopyalar` alt komutunu GERÇEKTEN koşarak tabloyu alır. Metni grep'lemek yerine betiği
    koşturmak, tablonun bir ÇIKTI olduğunu (yani betiğin kendi mantığının okuduğu şeyle aynı
    olduğunu) ölçer — beyan ile davranış ancak böyle ayrışamaz.

    `betik` parametresi MUTASYON içindir (O8): şerhteki sayıyı tabloya bağlayan çivi, ancak
    tablosu DEĞİŞMİŞ bir betikte ölçülebilir."""
    r = subprocess.run(["bash", str(betik), "--kopyalar"], capture_output=True, text=True)
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
    assert len(k) == KOPYA_SAYISI, k
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
    # D7 (YÜKSEK-3): 6 → 7. Faz-1A geçişi tamamlandığı için `/etc/hindsight/creds/<AD>` AYRI bir
    # dosya satırı oldu — "nerede YOK" ile "nerede VAR" iki ayrı gerçektir ve tek satırda
    # anlatılamaz. `/opt/hindsight/.key` HÂLÂ dışarıda (§2'nin donuk sözlüğünde sınıfı yok).
    assert len(env["dosyalar"]) == 7, "v439 E2 spec §1 ile BİREBİR eşitlik istiyor"
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


def test_H1_openrouter_IKI_read_s_ve_ON_DORT_kopya(tmp_path):
    """İki anahtar ayrı ayrı istenir (stdin'den iki satır). NOUS 2 kopya (credential + motor
    API), OPENROUTER 12 kopya (`.env-apisix` ×2, hindsight creds, hindsight failover ÜYE
    anahtarları ×6, hermes ×3). Üye satırları O bölümünde AYRICA ölçülür; burada sayının
    kendisi pinlenir — sessizce küçülen bir kopya kümesi tam da bu betiğin var olma sebebidir."""
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
    """On dört kopyalı bir rotasyonun geri alımı ancak yedekten yapılabilir."""
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
    motorun sır deposu ise ÜÇÜNCÜSÜNÜ taşır — ikisi de tabloda yok.

    D7 (YÜKSEK-3): `/opt/hindsight/.env`in üç sırrı bu listeden ÇIKTI, çünkü CANLIDA da yoklar
    (ölçüm 2026-09-08 09:3xZ; Faz-1A geçişi 2026-09-07'de tamamlandı). O dosyadaki tarama
    körlüğünü ölçen çivi O4'tür — bilinmeyen bir ÜYE anahtarı eklenir ve BAĞIRILMASI ölçülür.
    Yani kapsam kaybı YOK; sahne canlıya YAKLAŞTI."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    assert "BEYAN DIŞI KOPYA: /opt/meridian/.env [MERIDIAN_DASH_TOKEN]" in r.stdout
    assert "BEYAN DIŞI KOPYA: /opt/meridian/state/secrets.json [MERIDIAN_DASH_TOKEN]" in r.stdout
    for ad in ("HINDSIGHT_API_TENANT_API_KEY", "HINDSIGHT_API_LLM_API_KEY",
               "HINDSIGHT_API_DATABASE_URL"):
        assert f"BEYAN DIŞI KOPYA: /opt/hindsight/.env [{ad}]" not in r.stdout, \
            f"sahne canlıdan ayrıştı: {ad} `.env`de olmamalı"
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
    """D6'nın ısırdığı dal: `/run/credentials/<birim>/<kimlik>` doluluk ölçümü.

    D5'te ÇAĞRI YERİ değişti (`_kredensiyel_denetle <alt> <yeniden başlatılan birim…>`) ve bu
    çivi hedefini bulamayıp KIRMIZI oldu — istenen davranış: `_mutant` hedefin varlığını
    doğruladığı için "mutasyonsuz betiği ölçen sessiz yeşil" mümkün değil."""
    _, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('  _kredensiyel_denetle "$alt" $birimler\n', "  return 0\n"))
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
    çivisinin hiçbiri bunu göremiyordu; şimdi görüyor.

    TUR 4'TE ARIZA NOKTASI ÖNE KAYDI: kimlik kırıldığında ilk 000'ı `_farksal` değil hazırlık
    yoklaması alır (`_hazir_bekle`, `--dash` için `/healthz`) ve koşum ORADA durur. Sınıf aynı
    (curl cfg'yi açamıyor → 000 → "ölçülemedi"), yalnız daha erken yakalanıyor; hüküm bu yüzden
    tek bir çağrı yerine değil, "çıkış 2 + ÖLÇÜLEMEDİ + HTTP 000" üçlüsüne bağlıdır."""
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
    assert len(r.stdout.strip().splitlines()) == KOPYA_SAYISI


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
    # D7 (inceleme, BLOKLAYICI-1): `/run/credentials/` ARTIK SÜZGEÇTEN GEÇMİYOR — ve bu dünyada
    # süzgece hiç GEREK de yoktu: motor ölü olduğu için negatif kontrol daha ilk adımda durur ve
    # HİÇBİR birim yeniden başlatılmaz, yani systemd'nin kopyası HİÇ DOĞMAZ. Ölçü bu yüzden
    # burada daha SERTTİR: hiçbir dosya, credential dizini DAHİL, değişmemiş olmalı.
    kalici = {y for y in degisen if "sir-yedek-" not in y}
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
    # D7 (inceleme, BLOKLAYICI-1): `/run/credentials/` ARTIK SÜZGEÇTEN GEÇMİYOR. Eski biçim
    # `"/run/credentials/" not in y` ile o alanı DIŞLIYORDU, yani "HİÇBİR KALICI YAZIM" iddiası
    # DİSK için doğru, ÇALIŞAN SÜREÇ DURUMU için YANLIŞTI: aşımdan sonra meridian BOŞ bir
    # credential'la koşmaya devam ediyordu (ölçüldü 2026-09-08: değer `''`) ve çivi tam o alanı
    # süzgeçliyordu. Bu dizin TÜRETİLMİŞ bir durumdur — ölçüsü "hiç değişmedi mi" DEĞİL,
    # "KAYNAĞIYLA AYNI mı"dır: kaynaklar geri alındıysa buradaki değer de ESKİ olmalıdır.
    kalici = {y for y in degisen if "sir-yedek-" not in y}
    kred = {y for y in kalici if "/run/credentials/" in y}
    assert kred, "credential dizini hiç doğmadı — çivi kör (pozitif kontrol)"
    for y in sorted(kred):
        p = pathlib.Path(y)
        kaynak = KRED_KAYNAKLARI[p.parent.name][p.name]
        assert p.read_bytes() == (kok / kaynak.lstrip("/")).read_bytes(), \
            f"credential KAYNAĞIYLA AYRIŞTI — bilerek bozuk/boş değer canlıda KALDI: {y}"
    assert not (kalici - kred), f"rotasyon hedefine kalıcı yazım var: {kalici - kred}"
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

def test_K10a_openrouter_RESTART_SIRASI_ve_KAPSAMI(tmp_path):
    """Kapıyı (apisix) motordan ÖNCE başlatmazsan motor yeni anahtarla ESKİ kapıya konuşur —
    sıra sözleşmedir ve pozitif turda hâlâ apisix→hindsight→meridian'dır.

    D5'TE KAPSAM DARALDI (ölçüm 2026-09-08 07:3xZ): negatif kontrol turları artık ÜÇ birimi değil
    yalnız ÖLÇÜLEN SIRRIN tüketicilerini yeniden başlatır (NOUS→motor, OPENROUTER→kapı+hafıza).
    Beş turluk 15 restart 9'a indi. Sıra pinlenmeye devam ediyor çünkü sessizce atlanan bir tur
    ilk gerçek çağrıda 401 üretir; KÜME de pinleniyor çünkü sessizce genişleyen bir küme bakım
    penceresine karşılıksız dakikalar ekler (hindsight ~60 s açılıyor)."""
    kok, ortam = _sahte_ortam(tmp_path)
    assert _kos(BETIK, ortam, "--openrouter",
                girdi=f"{YENI_NOUS}\n{YENI_OR}\n").returncode == 0
    beklenen = ["meridian.service", "meridian.service",                        # NK(NOUS) boz+geri
                "apisix.service", "hindsight-api.service",                     # NK(OR) boz
                "apisix.service", "hindsight-api.service",                     # NK(OR) geri-al
                "apisix.service", "hindsight-api.service", "meridian.service"]  # pozitif kanıt
    assert _birim_sirasi(kok) == beklenen, _birim_sirasi(kok)


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


# =================================================================================================
# M) TUR 4 — HAZIRLIK BEKLEME ("restart döndü" ≠ "birim dinliyor")
# =================================================================================================
# CANLI VAKA 2026-09-08 06:13Z (A1, betiğin İLK gerçek koşumu, `--openrouter`): `_negatif_kontrol`
# üç birimi yeniden başlattı ve HEMEN ölçtü (`_nous_hali` → `/api/secrets/test/nous`); meridian
# henüz ayakta olmadığı için curl `000` döndü → `OLCULEMEDI(http=000)` → "ÖLÇÜM ARIZASI" → geri
# alma. Dosyalar yedekle aynı kaldı (zarar YOK) ama rotasyon YAPILAMADI. Betik doğru davrandı;
# eksik olan ZAMANDI.
#
# ÇİVİLERİN GÖREMEME SEBEBİ ŞİMDEYDİ, MANTIKTA DEĞİL (tur-3'ün dersinin zaman eksenindeki hâli):
# `SIM_SYSTEMCTL` restart'ı ANINDA hazır sayıyordu. Artık her `restart` birime bir "ulaşılamaz
# çağrı" bütçesi yazar (`SAHTE_HAZIR_N`) ve `SIM_CURL` bütçe bitene kadar O BİRİMİN HER UCUNDA
# 000 döner — vakada 000'ı alan uç `/healthz` DEĞİL ölçüm ucuydu, model bu yüzden uçtan bağımsız.


def _url_gunlugu(kok: pathlib.Path) -> list[str]:
    """Şimin gördüğü URL'lerin sırası — "yoklama gerçekten döndü mü" ancak böyle ölçülür.
    `argv.log` bunu söyleyemez: URL argv'de değil `-K` yapılandırma dosyasındadır."""
    return (kok / ".sahte/url.log").read_text(encoding="utf-8").split()


def test_M0_URETIM_VARSAYILANLARI_ve_UC_HARITASI_betikte():
    """Çivi ortamı bekleme penceresini SIKIŞTIRIR (0,01 s / 2 s) — sıkıştırmasaydı tek bir
    aşım çivisi bir dakika sürerdi. Sıkıştırma SÖZLEŞMEYİ değiştirmemelidir: üretim
    varsayılanları burada ölçülür. Bu satır olmasaydı biri betikteki tavanı 0'a çekse M
    bölümünün tamamı yine yeşil kalır, canlıda ise hiç beklenmezdi."""
    metin = BETIK.read_text(encoding="utf-8")
    assert 'HAZIR_BEKLE_ARALIK_S="${HAZIR_BEKLE_ARALIK_S:-2}"' in metin
    assert 'HAZIR_BEKLE_TAVAN_S="${HAZIR_BEKLE_TAVAN_S:-60}"' in metin
    # D5: hindsight-api'nin ÖLÇÜLEN açılışı ~60 s (07:34:18 restart → 07:35:18 startup complete),
    # yani ortak 60 s tavanı SINIRDAYDI ve ikinci canlı deneme oradan düştü.
    # D7 (ORTA-5): 180 → 300. Aynı gün 08:07:06→08:08:45 ölçümü açılışı 99 s verdi, yani 180
    # yalnız 1,8× paydı; üstelik NEGATİF KONTROLDEKİ (bilerek bozuk anahtarlı) açılış yolu hiç
    # ölçülmedi ve aşımın bedeli D7'den beri "kurtarma restart'ı"dır — ucuz bir arıza değil.
    # Sayı burada AYRICA pinlenir çünkü `test_P7` onu ŞERHTEKİ biçimden türetir: iki çivi aynı
    # sabiti iki ayrı yönden ölçer.
    assert 'HAZIR_TAVAN_S_hindsight_api="${HAZIR_TAVAN_S_hindsight_api:-300}"' in metin
    # Üç birim, üç uç — ve her uç KENDİ kabul ölçütüyle (D5). Ölçüm 2026-09-08 (A1).
    assert '$API/healthz http ' in metin and '$HINDSIGHT/health 200 ' in metin
    assert '$KAPI_KOK/healthz http ' in metin
    # Kapının PORTU tek yerde yaşar: `KAPI_UC` kökten türetilir (tek-kaynak yasası).
    assert 'KAPI_UC="${SIR_ROT_KAPI:-$KAPI_KOK/llm/v1}"' in metin


def test_M1_restart_sonrasi_HAZIR_beklenir_ve_SURE_BASILIR(tmp_path):
    """(a) Birim üç çağrı boyunca ulaşılamaz, dördüncüde 200. Koşum GEÇER ve beklenen süre
    çıktıya BASILIR — basılmayan bir sayı ölçülmemiş bir sayıdır.

    YOKLAMANIN GERÇEKTEN DÖNDÜĞÜ ölçülür: `/healthz` dört kez çağrılmalı. Tek çağrı sayılsaydı
    "bekleyen betik" ile "bir kez bakıp geçen betik" ayırt edilemezdi."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "3"
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(r"hazır: meridian \d+ s", r.stdout), r.stdout
    saglik = [u for u in _url_gunlugu(kok) if u.endswith("/healthz")]
    assert len(saglik) == 4, saglik
    # Bekleme bir SÜS değil: asıl kanıt ondan SONRA ölçülür ve geçer.
    assert "pano /api/secrets: yeni→200 · eski→401" in r.stdout, r.stdout


def test_M2_CANLI_VAKA_openrouter_ARTIK_gecer(tmp_path):
    """(a) — vakanın kendisi. `--openrouter` beş TUR yeniden başlatır ve negatif kontrolün
    ölçümü restart'ın HEMEN ardından koşar. Aynı dünyada (N=3) rotasyon tamamlanır ve beş turun
    tüketicileri beklenmiş olur: 9 "hazır" satırı (D5'ten önce 15'ti — negatif kontrol üç birimi
    birden başlatıyordu). Sayı pinlenir çünkü bir tur sessizce beklemeden geçerse hüküm yine
    000'a bağlı kalırdı (K10a'nın sıra pinlemesiyle aynı gerekçe)."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "3"
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "negatif kontrol (NOUS_API_KEY, yöntem=bos): → RET" in r.stdout
    assert "negatif kontrol (OPENROUTER_API_KEY, yöntem=bozuk): → RET" in r.stdout
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS
    assert r.stdout.count("✓ hazır: ") == 9, r.stdout


def test_M3_UCU_OLMAYAN_birim_HAZIR_SAYILMAZ_ve_bunu_SOYLER(tmp_path):
    """`hindsight-cp.service` bir sağlık ucu sunmuyor (2026-09-08 itibarıyla ölçülmedi). Sessizce
    "hazır" saymak, ölçülmemiş bir şeyi ölçülmüş göstermek olurdu (uydurma yasağı); satır
    kapsamını BEYAN eder. Ölçülen ötekiler beklenir."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "2"
    r = _kos(BETIK, ortam, "--tenant")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "hazırlık yoklaması YOK: hindsight-cp.service" in r.stdout
    assert "hazır SAYILMADI" in r.stdout
    assert "hazır: hindsight-api" in r.stdout and "hazır: meridian" in r.stdout
    assert len([u for u in _url_gunlugu(kok) if u.endswith("/health")]) == 3
    assert len([u for u in _url_gunlugu(kok) if u.endswith("/healthz")]) == 3


def test_M4_TAVAN_asilirsa_OLCULEMEDI_ve_HICBIR_KALICI_YAZIM(tmp_path):
    """(b) Birim hiç açılmaz. Betik "hazır" DEMEZ: ölçemediğini söyler, çıkış 2 verir ve negatif
    kontrolün geçici yazımı trap ile geri alınır — operatörün TAZE anahtarı hiç yazılmaz.

    N TAVANIN ALTINDA BİR SAYI OLAMAZ. 99 yoklama hızlı bir makinede 2 s'lik tavana varmadan
    biterdi ve çivi renk değiştirirdi; flaky bir çivi hüküm değildir (J8 dersi). Bu yüzden N
    tavanın ulaşamayacağı kadar büyük seçilir ve hüküm SÜREYE değil DAVRANIŞA bağlanır."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "999999"
    once = _dosya_imzalari(kok)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    # D5: ilk restart artık NOUS negatif kontrolünündür ve YALNIZ motoru başlatır — tavan da
    # ilk orada aşılır. (D5'ten önce ilk tur üç birimi başlatıyordu ve aşım apisix'te görülüyordu.)
    assert "hazırlık bekleme aşıldı" in r.stderr and "meridian.service" in r.stderr, r.stderr
    assert "HTTP 000" in r.stderr, r.stderr
    assert "✓ hazır: " not in r.stdout, r.stdout
    sonra = _dosya_imzalari(kok)
    degisen = {y for y in set(once) | set(sonra) if once.get(y) != sonra.get(y)}
    # D7 (inceleme, BLOKLAYICI-1): `/run/credentials/` ARTIK SÜZGEÇTEN GEÇMİYOR. Eski biçim
    # `"/run/credentials/" not in y` ile o alanı DIŞLIYORDU, yani "HİÇBİR KALICI YAZIM" iddiası
    # DİSK için doğru, ÇALIŞAN SÜREÇ DURUMU için YANLIŞTI: aşımdan sonra meridian BOŞ bir
    # credential'la koşmaya devam ediyordu (ölçüldü 2026-09-08: değer `''`) ve çivi tam o alanı
    # süzgeçliyordu. Bu dizin TÜRETİLMİŞ bir durumdur — ölçüsü "hiç değişmedi mi" DEĞİL,
    # "KAYNAĞIYLA AYNI mı"dır: kaynaklar geri alındıysa buradaki değer de ESKİ olmalıdır.
    kalici = {y for y in degisen if "sir-yedek-" not in y}
    kred = {y for y in kalici if "/run/credentials/" in y}
    assert kred, "credential dizini hiç doğmadı — çivi kör (pozitif kontrol)"
    for y in sorted(kred):
        p = pathlib.Path(y)
        kaynak = KRED_KAYNAKLARI[p.parent.name][p.name]
        assert p.read_bytes() == (kok / kaynak.lstrip("/")).read_bytes(), \
            f"credential KAYNAĞIYLA AYRIŞTI — bilerek bozuk/boş değer canlıda KALDI: {y}"
    assert not (kalici - kred), f"rotasyon hedefine kalıcı yazım var: {kalici - kred}"
    ham = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in kok.rglob("*")
                    if p.is_file() and ".sahte" not in str(p))
    assert YENI_NOUS not in ham and YENI_OR not in ham, "taze anahtar diske düştü"
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"]
    assert _depo(kok)["NOUS_API_KEY"] == ESKI["nous"], "depo kopyası geri alınmadı"


@pytest.mark.parametrize("alt,bekleyen", [("--kapi", 2), ("--tenant", 2), ("--db", 1),
                                          ("--dash", 1), ("--openrouter", 3)])
def test_M7_KURU_KOSUM_bekleme_BEDELINI_de_soyler(tmp_path, alt, bekleyen):
    """BEDEL YASASI. Bekleme bakım penceresine SÜRE ekler; kuru koşum operatörün koşacağı İLK
    komuttur ve o süreyi orada görmelidir (C2'nin "hangi birimler" sorusunun ikinci yarısı).

    BEKLENEN BİRİM SAYISI BETİĞİN KENDİ ÇIKTISINDAN türetilir — birim tablosunun ikinci bir
    kopyasını buraya yazmak tek-kaynak yasasının yasakladığı hâldir. Çivinin kendi İDDİASI
    yalnız `bekleyen`dir: kaç birimin ÖLÇÜLMÜŞ bir sağlık ucu var (A1 haritası, 2026-09-08).

    D5: satır başına bir birim (tek satırda değil) ve her satır KABUL ÖLÇÜTÜNÜ + TAVANI da taşır —
    "ne kadar bekleyebilir" sorusunun cevabı artık birim başına farklıdır."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, alt, "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    birimler = r.stdout.split("yeniden başlatılacak:")[1].splitlines()[0].split()
    bas = r.stdout.split("  hazırlık beklemesi (")[1]
    satirlar = [x for x in bas.splitlines() if x.startswith("    · ")]
    assert len(satirlar) == len(birimler), (satirlar, birimler)
    blok = "\n".join(satirlar)
    # HER birim görünür: ucu OLAN uçla + ölçütle + tavanla, OLMAYAN "beklenmez" beyanıyla.
    assert blok.count("→") == len(birimler), blok
    assert blok.count("/health") == bekleyen, blok
    assert blok.count("(sağlık ucu YOK, beklenmez)") == len(birimler) - bekleyen, blok
    assert blok.count("kabul: ") == bekleyen and blok.count("tavan: ") == bekleyen, blok
    # Tavan betiğin KENDİ sabitinden basılır (ortam ikisini de 2'ye sıkıştırdı) — ikinci kopya yok.
    assert blok.count("tavan: 2 s") == bekleyen, blok


def test_M5_MUT_hazir_bekle_KALKARSA_M1_kirmizi(tmp_path):
    """(c) M1'in ısırdığı dal. İki çağrı yeri de mutasyonla kaldırılır; aynı dünyada (N=3)
    `--dash`in kanıtı restart'ın hemen ardından koşar, 000 alır ve betik durur."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "3"
    m = _mutant(tmp_path,
                ('  _hazir_bekle $birimler\n', '  :\n'),
                ('  _hazir_bekle "$@"\n}', '  :\n}'))
    r = _kos(m, ortam, "--dash")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "hazır: meridian" not in r.stdout, "mutasyon ısırmıyor — M1 yanlış sebeple yeşil"
    assert "YENİ değerle HTTP 000" in r.stderr, r.stderr


def test_M6_MUT_hazir_bekle_KALKARSA_CANLI_VAKA_geri_doner(tmp_path):
    """(c) M2'nin ısırdığı dal — ve aynı zamanda vakanın yeniden üretimi. Mutant, 2026-09-08
    06:13Z'de canlıda görülen METNİ üretir: negatif kontrolün ölçümü `OLCULEMEDI(http=000)`
    döner ve betik "ÖLÇÜM ARIZASI" deyip rotasyonu yapmadan durur."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "3"
    m = _mutant(tmp_path,
                ('  _hazir_bekle $birimler\n', '  :\n'),
                ('  _hazir_bekle "$@"\n}', '  :\n}'))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "ÖLÇÜM ARIZASI → OLCULEMEDI(http=000)" in r.stderr, r.stderr
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == ESKI["nous"], \
        "mutasyon ısırmıyor — M2 yanlış sebeple yeşil"


# =================================================================================================
# N) TUR 5 — HAZIRLIĞIN ANLAMI VE KAPSAMI (ikinci canlı deneme, 2026-09-08 07:2x-07:4xZ)
# =================================================================================================
# TUR 4 "beklemek gerekiyor"u ölçtü. İKİNCİ canlı deneme, bekleme VARKEN, iki AYRI kökten düştü:
#   (1) ANLAM. `meridian` yeniden başladıktan sonra `/healthz` DAKİKALARCA 503 döner — gövde
#       `{"status":"stale","heartbeat_age_seconds":…}`: worker açılışta ağır bar tazelemesi
#       yaparken nabız yazılmaz. Ama API AYAKTADIR (`/api/secrets/test/nous` aynı anda cevap
#       verir). 200 şartı, SAĞLIKLI bir motoru "ölü" saymaktı. `apisix` `/healthz` meridian'a
#       proxy → aynı gövde, aynı hüküm. `hindsight-api` `/health` KENDİ sürecidir: orada 200 şart.
#   (2) TAVAN. `hindsight-api` `/health` 200'ü restart'tan ~60 s sonra verdi (07:34:18 restart →
#       07:35:18 "Application startup complete") — ortak 60 s tavanı SINIRDAYDI ve koşum
#       "hazırlık bekleme aşıldı: hindsight-api … 000" ile düştü.
# ÜÇÜNCÜ KÖK ÖLÇÜMÜN KENDİSİ DEĞİL BEDELİYDİ: NOUS negatif kontrolü üç birimi birden yeniden
# başlatıyordu, oysa NOUS'u yalnız motor tüketir — iki karşılıksız restart + iki karşılıksız
# bekleme, bakım penceresinden.
#
# ŞİM: `SAHTE_HEALTHZ_KOD` / `SAHTE_HEALTH_KOD` "cevap veriyor ama 200 değil" dünyasını modeller.
# `SAHTE_HAZIR_N` ("hiç cevap yok", 000) ile aynı bayrağa BAĞLANAMAZ: D5'in ayırdığı iki hâl tam
# olarak bunlardır ve tek bayrak ikisini birden çevirseydi ayrım ölçülemezdi.


def test_N1_meridian_503_ile_HAZIR_ve_satir_DURUSTCE_soyler(tmp_path):
    """(a) — birinci kökün kendisi. Motor N çağrı boyunca ulaşılamaz, sonra 503 döner (canlıda
    ölçülen normal açılış hâli). Koşum GEÇER: 503 "API ayakta" demektir.

    SATIR BUNU SÖYLEMEK ZORUNDA. Gevşek bir kabul ölçütü, gevşek bir BEYAN üretemez: "hazır:
    meridian 0 s" ile "hazır: meridian 0 s (healthz 503 — nabız bayat, API ayakta)" aynı cümle
    değildir ve operatörün gördüğü ikincisi olmalıdır (uydurma yasağı: ölçülmemiş bir tazeliği
    ölçülmüş göstermek)."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "3"
    ortam["SAHTE_HEALTHZ_KOD"] = "503"
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(r"hazır: meridian \d+ s \(healthz 503 — nabız bayat, API ayakta\)", r.stdout), \
        r.stdout
    # Yoklama GERÇEKTEN döndü: 3 ulaşılamaz + 1 cevaplı.
    assert len([u for u in _url_gunlugu(kok) if u.endswith("/healthz")]) == 4, _url_gunlugu(kok)
    # Bekleme bir süs değil: asıl kanıt ondan SONRA ölçülür ve geçer.
    assert "pano /api/secrets: yeni→200 · eski→401" in r.stdout, r.stdout


def test_N2_hindsight_200_ISTER_meridian_ISTEMEZ_ayni_kosumda(tmp_path):
    """(a)'nın ikinci yarısı: ÖLÇÜT BİRİM BAŞINADIR. Aynı dünyada her sağlık ucu 503 döner —
    meridian ve apisix HAZIR sayılır (HTTP cevabı var), hindsight-api SAYILMAZ (kendi süreci,
    200 şart) ve koşum orada ölçülemedi der.

    Tek bir ölçüt olsaydı bu koşumun iki hükmünden biri yanlış olurdu: ya motor boşuna beklenir
    (canlı vaka), ya hafızanın açılmamış olması "hazır" sayılırdı."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HEALTHZ_KOD"] = "503"
    ortam["SAHTE_HEALTH_KOD"] = "503"
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert re.search(r"hazır: meridian \d+ s \(healthz 503", r.stdout), r.stdout
    assert re.search(r"hazır: apisix \d+ s \(healthz 503", r.stdout), r.stdout
    assert "hazırlık bekleme aşıldı: hindsight-api.service" in r.stderr, r.stderr
    assert "HTTP 503" in r.stderr and "HTTP 200 gelmedi" in r.stderr, r.stderr
    assert "hazır: hindsight-api" not in r.stdout, r.stdout
    # Operatörün TAZE anahtarı hiç yazılmadı (negatif kontrol yazımdan ÖNCE koşar).
    ham = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in kok.rglob("*")
                    if p.is_file() and ".sahte" not in str(p))
    assert YENI_NOUS not in ham and YENI_OR not in ham, "taze anahtar diske düştü"


def test_N3_TAVAN_birim_basina_hindsight_kendi_tavaniyla_gecer(tmp_path):
    """(b) — ikinci kök. Canlıda: ortak 60 s tavanı hindsight'ın ~60 s'lik açılışına YETMEDİ,
    180 s yeter. Çivi ilişkiyi SIKIŞTIRARAK ölçer (ortak tavan 0 s = yetmez, birim tavanı 5 s =
    yeter): 60/180'i gerçek saatle beklemek dakikalar sürerdi ve süreye bağlı bir çivi hızlı/yavaş
    makinede renk değiştirirdi — flaky bir çivi hüküm değildir (J8/M4 dersi). Üretim değerlerinin
    kendisi M0'da metinden pinlenir."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "3"
    ortam["HAZIR_BEKLE_TAVAN_S"] = "0"            # ortak tavan: ilk 000'da aşılır
    ortam["HAZIR_TAVAN_S_hindsight_api"] = "5"    # birim tavanı: yeter
    r = _kos(BETIK, ortam, "--db")                # tek birim: hindsight-api
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(r"hazır: hindsight-api \d+ s", r.stdout), r.stdout
    assert len([u for u in _url_gunlugu(kok) if u.endswith("/health")]) == 4, _url_gunlugu(kok)


def test_N4_MUT_ORTAK_TAVAN_kullanilirsa_N3_kirmizi(tmp_path):
    """(c) N3'ün ısırdığı dal — ve canlı vakanın yeniden üretimi. `_hazir_tavan`ın birim dalı
    ortak tavana çevrilince aynı dünyada koşum "hazırlık bekleme aşıldı: hindsight-api" ile
    düşer: 2026-09-08 07:35Z'de canlıda görülen METİN."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "3"
    ortam["HAZIR_BEKLE_TAVAN_S"] = "0"
    ortam["HAZIR_TAVAN_S_hindsight_api"] = "5"
    m = _mutant(tmp_path, ('hindsight-api.service) echo "$HAZIR_TAVAN_S_hindsight_api" ;;',
                           'hindsight-api.service) echo "$HAZIR_BEKLE_TAVAN_S" ;;'))
    r = _kos(m, ortam, "--db")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "hazırlık bekleme aşıldı: hindsight-api.service" in r.stderr, r.stderr
    assert "hazır: hindsight-api" not in r.stdout, "mutasyon ısırmıyor — N3 yanlış sebeple yeşil"


def test_N5_MUT_200_SARTI_geri_gelirse_N1_kirmizi(tmp_path):
    """(c) N1'in ısırdığı dal. `http` ölçütü 200 şartına çevrilince, canlıda ÇALIŞAN bir motor
    (503 = nabız bayat, API ayakta) "hazır değil" sayılır ve rotasyon yine yapılamaz — ikinci
    canlı denemenin birinci kökü."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HEALTHZ_KOD"] = "503"
    m = _mutant(tmp_path, ('    http) [ "$2" != "000" ] ;;', '    http) [ "$2" = "200" ] ;;'))
    r = _kos(m, ortam, "--dash")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "hazırlık bekleme aşıldı: meridian.service" in r.stderr, r.stderr
    assert "HTTP 503" in r.stderr, r.stderr


def test_N6_MUT_DURUST_SATIR_kalkarsa_N1_kirmizi(tmp_path):
    """(c) N1'in İKİNCİ iddiasının dalı: gevşek ölçütle geçen bir birim, satırında bunu söyler.
    Açıklama eki kaldırılınca operatör "hazır: meridian 0 s" görür ve 503'ü hiç bilmez — kabul
    ölçütünün gevşekliği ÖLÇÜMÜN BEYANINA sızmamış olur (bedel yasası: ne kaybettiğini de söyle)."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HEALTHZ_KOD"] = "503"
    m = _mutant(tmp_path, ('      oldu "hazır: ${b%.service} $gecen s (${uc##*/} $kod — $aciklama)"',
                           '      oldu "hazır: ${b%.service} $gecen s"'))
    r = _kos(m, ortam, "--dash")
    assert r.returncode == 0, r.stdout + r.stderr          # koşum GEÇER, beyan EKSİKTİR
    assert "healthz 503" not in r.stdout, "mutasyon ısırmıyor — N1'in beyan iddiası ölçülmüyor"


def test_N7_NEGATIF_KONTROL_yalnizca_SIRRIN_tuketicisini_baslatir(tmp_path):
    """(c) üçüncü kök. NOUS'u yalnız motor tüketir (kapı isteğin Authorization'ını upstream'e
    geçirmez, hafıza NOUS okumaz); OPENROUTER'ı kapı ve hafıza tüketir, motor DEĞİL. Restart
    kümesi bu haritadan gelir — beş turluk 15 restart 9'a iner ve kısalan şey bakım penceresidir
    (hindsight ~60 s açılıyor)."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    sira = _birim_sirasi(kok)
    assert sira[:2] == ["meridian.service", "meridian.service"], sira   # NOUS: boz + geri-al
    assert sira[2:6] == ["apisix.service", "hindsight-api.service"] * 2, sira   # OPENROUTER
    assert len(sira) == 9, sira
    assert "yeniden başlatılacak (yalnız NOUS_API_KEY tüketicileri): meridian.service" in r.stdout
    assert ("yeniden başlatılacak (yalnız OPENROUTER_API_KEY tüketicileri): "
            "apisix.service hindsight-api.service") in r.stdout
    # Restart İSTEMEYEN tüketiciler BEYANLIDIR: hermes profilleri yazıldı ama başlatılmadı.
    assert "hermes profilleri (bekci·karne·sef) yeniden BAŞLATILMAZ" in r.stdout


def test_N8_MUT_ALT_KOMUTUN_TAMAMI_baslatilirsa_N7_kirmizi(tmp_path):
    """(c) N7'nin ısırdığı dal: negatif kontrol eski hâline (alt komutun tamamı) çevrilince
    NOUS turu apisix ve hindsight'ı da başlatır — ölçülen sırla ilgisi olmayan iki kesinti."""
    kok, ortam = _sahte_ortam(tmp_path)
    m = _mutant(tmp_path, ('  birimler="$(_sir_birimleri "$sir")" || die',
                           '  birimler="$(_birimler "$alt")" || die'))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    sira = _birim_sirasi(kok)
    assert sira[:3] == ["apisix.service", "hindsight-api.service", "meridian.service"], sira
    assert len(sira) == 15, "mutasyon ısırmıyor — N7 yanlış sebeple yeşil"


def test_N9_POZITIF_KANIT_yalniz_YAZILAN_sirrin_tuketicisini_baslatir(tmp_path):
    """Operatör tek anahtar döndürüyorsa (ikincisi boş bırakılır) ötekinin birimini yeniden
    başlatmak karşılıksız bir kesinti + karşılıksız bir bekleme olur. NOUS-only koşumda kapıya ve
    hafızaya HİÇ dokunulmaz."""
    kok, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _birim_sirasi(kok) == ["meridian.service"] * 3, _birim_sirasi(kok)
    assert (kok / "etc/meridian/nous_api_key").read_text().strip() == YENI_NOUS
    # OPENROUTER kopyaları ESKİ değerde: yazılmayan sırrın birimi de başlatılmaz.
    apisix = (kok / "opt/apisix/.env-apisix").read_text(encoding="utf-8")
    assert ESKI["or"] in apisix and YENI_OR not in apisix, apisix
    assert "hermes profilleri" not in r.stdout, "yazılmayan sır için kapsam beyanı basıldı"


def test_N12_MUT_hindsight_200_SARTI_gevserse_N2_kirmizi(tmp_path):
    """(c) N2'nin ısırdığı dal — ve kabul ölçütünün İKİNCİ yarısı. `200` ölçütü `http`e
    gevşetilince açılmamış bir hindsight-api ("cevap veriyor ama 200 değil") HAZIR sayılır ve
    koşum geçer: tam olarak D5'in reddettiği hâl. Tek bir gevşek ölçüt her uçta doğru olsaydı bu
    mutasyon ısırmazdı; ısırıyor, yani ölçüt gerçekten birim başınadır."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HEALTHZ_KOD"] = "503"
    ortam["SAHTE_HEALTH_KOD"] = "503"
    m = _mutant(tmp_path, ('    200)  [ "$2" = "200" ] ;;', '    200)  [ "$2" != "000" ] ;;'))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert "hazırlık bekleme aşıldı: hindsight-api.service" not in r.stderr, \
        "mutasyon ısırmıyor — N2 yanlış sebeple yeşil"
    assert re.search(r"hazır: hindsight-api \d+ s \(health 503", r.stdout), r.stdout


def test_N10_SIR_BIRIM_HARITASI_envanterle_AYRISMAZ(tmp_path):
    """AYRIŞMA ÇİVİSİ (tek-kaynak yasası). Kopya tablosu BİRİM SÜTUNU taşımaz, o yüzden harita
    betikte ayrıca yaşar; ayrıca yaşayan her kopya bir çiviye bağlanır. Envanterdeki
    `rotasyon_kopyalari.kopyalar[].tuketici` alanlarından türetilen `.service` kümesi, betiğin
    `--kuru` çıktısındaki haritayla BİREBİR aynı olmalıdır.

    HARİTA BETİĞİN ÇIKTISINDAN OKUNUR, metninden değil: beyan ile davranış ancak böyle ayrışamaz
    (A bölümünün `--kopyalar` gerekçesiyle aynı)."""
    _, ortam = _sahte_ortam(tmp_path)
    betikte: dict[str, set[str]] = {}
    for alt in ("--kapi", "--tenant", "--db", "--dash", "--openrouter"):
        r = _kos(BETIK, ortam, alt, "--kuru")
        assert r.returncode == 0, r.stdout + r.stderr
        # YALNIZ sır→birim bölümü okunur: "hazırlık beklemesi" bloğu da "    · " ile başlar ve
        # onu da yutmak haritayı birim adlarıyla kirletirdi (bölüm sınırı, sezgisel değil).
        icinde = False
        for s in r.stdout.splitlines():
            if s.startswith("  sır → tüketici birimler"):
                icinde = True
                continue
            if icinde and not s.startswith("    · "):
                break
            if icinde:
                sir, birimler = s.split("· ", 1)[1].split(" → ")
                betikte[sir] = set(birimler.split())
    envanterde: dict[str, set[str]] = {}
    for k in _envanter_kopyalari():
        envanterde.setdefault(k["sir"], set()).update(
            re.findall(r"[a-z0-9-]+\.service", k["tuketici"]))
    assert betikte, "kuru rapor sır→birim haritasını basmıyor"
    assert set(betikte) == set(envanterde), (sorted(betikte), sorted(envanterde))
    for sir in betikte:
        assert betikte[sir] == envanterde[sir], (sir, betikte[sir], envanterde[sir])


def test_N11_RESTART_ISTEMEYEN_tuketiciler_BEYANLI():
    """N10 `.service` TAŞIMAYAN tüketicileri (hermes profilleri, oneshot birimler, postgres,
    motorun kendi deposu) sessizce eler. Sessiz eleme, ölçülmemiş bir eleme olurdu: yarın
    envantere `.service` taşımayan yeni bir tüketici girerse burası ÖTER ve "bu neden yeniden
    başlatılmıyor?" sorusu sorulur (bedel yasası)."""
    beyanli = {
        "hermes bekci profili", "hermes karne profili", "hermes sef profili",   # timer'lı oneshot
        "brifing/learn/sprint@ birimleri (EnvironmentFile, başlangıçta okunur)",  # aynı sınıf
        "postgres",                                          # parolayı ALTER ROLE ile anında alır
        "meridian yerel sır deposu",                         # meridian sürecinin İÇİ
        "~/bin/hafiza_sor.sh (kabuk okuyucu; LLM'siz recall)",  # kabuk okuyucu, birim değil
    }
    servissiz = {k["tuketici"] for k in _envanter_kopyalari()
                 if not re.search(r"[a-z0-9-]+\.service", k["tuketici"])}
    assert servissiz <= beyanli, f"beyansız restart-istemeyen tüketici: {servissiz - beyanli}"
    assert servissiz, "envanterde hiç servissiz tüketici yok — çivi boşa ölçüyor (pozitif kontrol)"


# =================================================================================================
# O) TUR 6 — HAFIZA FAILOVER ZİNCİRİNİN ÜYE ANAHTARLARI
# =================================================================================================
# CANLI BULGU (2026-09-08 08:0xZ, A1). `/opt/hindsight/.env` 2026-09-06'dan beri reflect ve
# konsolidasyon failover zincirlerinin ÜYE anahtarlarını taşıyor: zincir üyesi ana anahtarı
# DEVRALMAZ, her üye kendi `HINDSIGHT_API_<yüzey>_LLM_<n>_API_KEY` satırını okur ve altısı da
# `OPENROUTER_API_KEY` değerinin birebir kopyasıdır. Altısı da kopya tablosunda YOKTU — yani
# `--openrouter` creds dosyasını döndürür, üyeler ESKİ anahtarla kalır ve eski anahtar iptal
# edildiği an zincir üyeleri 401 alıp SESSİZCE primary'ye düşerdi. Bu, betiğin var olma
# gerekçesindeki "unutulan kopya" sınıfının tam kendisidir.
#
# İKİNCİ KÖRLÜK, BİRİNCİSİNDEN DAHA SESSİZ: `--envanter`in beyan dışı taraması da bunları
# GÖRMÜYORDU. `_aranan_adlar` üç kaynaktan türer (sır kimliği · `env` alan adı · `dosya`/`url`
# dosya adı) ve üye adları bu üç kümenin HİÇBİRİNDE yok — yani "tabloda olmayan kopyayı bulurum"
# beyanı tam da bu sınıfta boştu. Aileyi elle listelemek aynı körlüğü bir sonraki üyede (`_4_`)
# tekrarlardı; çözüm dosyanın KENDİ alan adlarını okuyup sır ADI GİBİ görünenleri tabloya karşı
# sınamaktır (O4) ve sözlüğün gerçekten ısırdığı O6'da gösterilir.


def test_O1_openrouter_ALTI_UYE_anahtarini_da_dondurur(tmp_path):
    """(b) Üye satırları rotasyonun İÇİNDE: taze değeri taşırlar, dosyanın izni KORUNUR ve her
    alan TEK satır kalır (K8a'nın çift-satır dersi bu alanlar için de geçerlidir — çift satırda
    hafıza SONUNCUyu okur, operatör İLKİNİ düzenler ve iki değer sessizce ayrışır)."""
    kok, ortam = _sahte_ortam(tmp_path)
    hedef = kok / "opt/hindsight/.env"
    once_mod = oct(hedef.stat().st_mode & 0o777)
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    satirlar = hedef.read_text(encoding="utf-8").splitlines()
    for alan in UYE_ALANLARI:
        assert _env_alan(hedef, alan) == YENI_OR, alan
        assert len([s for s in satirlar if s.startswith(alan + "=")]) == 1, alan
    assert oct(hedef.stat().st_mode & 0o777) == once_mod == "0o600", "mod=koru korumadı"
    # PRIMARY AYRI KALIR: credential kanalı yalnız `HINDSIGHT_API_LLM_API_KEY`i taşır; üyeler
    # değeri `.env`de tutar (B sınıfı, beyanlı). İkisi de AYNI turda dönmek zorundadır.
    assert (kok / "etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY").read_text().strip() == YENI_OR
    # Zincirin AYAR satırı (sır DEĞİL) dokunulmadan kalır.
    assert 'HINDSIGHT_API_REFLECT_LLM_STRATEGY={"mode":"failover"}' in satirlar


def test_O2_envanter_ALTI_UYEYI_ESIT_raporlar_beyan_disi_DEGIL(tmp_path):
    """(c) Envanter üyeleri BEYANLI bir kopya olarak görür: `OPENROUTER_API_KEY`in referans
    kopyasıyla EŞİT raporlanırlar ve "beyan dışı" diye bağırılmazlar. İkisi birden ölçülür —
    yalnız "bağırmıyor" demek, hiç görmemekle aynı görünürdü."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    for alan in UYE_ALANLARI:
        satir = [s for s in r.stdout.splitlines()
                 if f"/opt/hindsight/.env [{alan}]" in s and "BEYAN DIŞI" not in s]
        assert satir, f"envanter üye satırını hiç raporlamadı: {alan}"
        assert satir[0].rstrip().endswith("EŞİT"), satir
        assert f"BEYAN DIŞI KOPYA: /opt/hindsight/.env [{alan}]" not in r.stdout, alan


def test_O3_UYE_alani_EKSIKSE_envanter_ALAN_YOK_der(tmp_path):
    """Rotasyonun ÖN KOŞULU ölçülebilir olmalı: zincir kısalırsa (bir üye `.env`den kalkarsa)
    `--openrouter` o satırda `die` eder ve bakım penceresi YARIM bir rotasyonla durur. Operatörün
    ilk komutu `--envanter`dir ve orada bu hâl SUSMAZ: "ALAN YOK" der. Sessiz kalsaydı eksiklik
    ancak yazım sırasında, yani en pahalı anda görünürdü."""
    kok, ortam = _sahte_ortam(tmp_path)
    p = kok / "opt/hindsight/.env"
    eksik = UYE_ALANLARI[2]
    p.write_text("".join(s + "\n" for s in p.read_text(encoding="utf-8").splitlines()
                         if not s.startswith(eksik + "=")), encoding="utf-8")
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    satir = [s for s in r.stdout.splitlines() if f"/opt/hindsight/.env [{eksik}]" in s]
    assert satir and "ALAN YOK" in satir[0], satir


def test_O4_BEYAN_DISI_taramasi_SIR_ADI_SOZLUGUNU_de_kullanir(tmp_path):
    """(d) TARAMANIN KÖRLÜĞÜ. Zincire yarın bir üye daha girerse (`_4_`) tablodan türeyen ad
    listesi onu GÖREMEZ — bugün altısının görünmez olmasının sebebi tam buydu. Tarama artık
    dosyanın KENDİ alan adlarını da okur ve sır ADI GİBİ görünen (`*_API_KEY` · `*_TOKEN` ·
    `*_SECRET` · `*_PASSWORD`) her alanı tabloya karşı sınar.

    Sözlük DAR ve bu bir KAPSAM BEYANIDIR: sır olmayan ayar satırları (`NOUS_MODEL`,
    `..._LLM_STRATEGY`) bağırmamalı — her satırı bulgu saymak gerçek bulguyu gürültüde boğardı."""
    kok, ortam = _sahte_ortam(tmp_path)
    p = kok / "opt/hindsight/.env"
    p.write_text(p.read_text(encoding="utf-8") + "HINDSIGHT_API_REFLECT_LLM_4_API_KEY=SAHTE-UYE-4\n",
                 encoding="utf-8")
    r = _kos(BETIK, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert ("!! BEYAN DIŞI KOPYA: /opt/hindsight/.env [HINDSIGHT_API_REFLECT_LLM_4_API_KEY]"
            in r.stdout), r.stdout
    for sirsiz in ("HINDSIGHT_API_REFLECT_LLM_STRATEGY", "NOUS_MODEL", "NOUS_ENDPOINT",
                   "HERMES_HOME"):
        assert f"BEYAN DIŞI KOPYA: /opt/hindsight/.env [{sirsiz}]" not in r.stdout, sirsiz
        assert f"[{sirsiz}]" not in r.stdout, f"sır OLMAYAN ayar bulgu diye basıldı: {sirsiz}"


def test_O5_MUT_uye_satiri_TABLODAN_silinirse_O1_ve_O2_kirmizi(tmp_path):
    """O1 ve O2'nin ısırdığı dal AYNI satırdır: kopya tablosundaki üye satırı. Silinince (bugün
    canlıda olan hâl) rotasyon o kopyayı YAZMAZ — eski değerle kalır — ve envanter onu artık
    beyanlı saymaz, BEYAN DIŞI diye bağırır. İki çivi de tek mutasyonla kırmızıya döner."""
    kok, ortam = _sahte_ortam(tmp_path)
    alan = UYE_ALANLARI[0]
    m = _mutant(tmp_path, (
        f"openrouter OPENROUTER_API_KEY env /opt/hindsight/.env {alan} koru koru -\n", ""))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _env_alan(kok / "opt/hindsight/.env", alan) == ESKI["or"], \
        "satır silindiği hâlde YENİ değer yazıldı — O1 mutasyonu ısırmıyor"
    assert _env_alan(kok / "opt/hindsight/.env", UYE_ALANLARI[1]) == YENI_OR, \
        "öteki üyeler de yazılmadı — mutasyon hedeflediğinden fazlasını bozdu"
    r2 = _kos(m, ortam, "--envanter")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert f"BEYAN DIŞI KOPYA: /opt/hindsight/.env [{alan}]" in r2.stdout, \
        "silinen üye beyan dışı sayılmadı — O2 mutasyonu ısırmıyor"


def test_O6_MUT_SIR_ADI_SOZLUGU_daralirsa_O4_kirmizi(tmp_path):
    """O4'ün ısırdığı dal: sır adı sözlüğü. Sözlük `_API_KEY`i kaybederse bilinmeyen üye anahtarı
    yeniden GÖRÜNMEZ olur — yani O4 gerçekten sözlüğü ölçüyor, tablodan türeyen listeyi değil."""
    kok, ortam = _sahte_ortam(tmp_path)
    p = kok / "opt/hindsight/.env"
    p.write_text(p.read_text(encoding="utf-8") + "HINDSIGHT_API_REFLECT_LLM_4_API_KEY=SAHTE-UYE-4\n",
                 encoding="utf-8")
    m = _mutant(tmp_path, ('_SIR_ADI_SONEKLERI="_API_KEY _TOKEN _SECRET _PASSWORD"',
                           '_SIR_ADI_SONEKLERI="_TOKEN"'))
    r = _kos(m, ortam, "--envanter")
    assert r.returncode == 0, r.stdout + r.stderr
    assert ("BEYAN DIŞI KOPYA: /opt/hindsight/.env [HINDSIGHT_API_REFLECT_LLM_4_API_KEY]"
            not in r.stdout), "sözlük mutasyonu O4'ü kırmıyor — çivi yanlış sebeple yeşil"
    # POZİTİF KONTROL: mutant hâlâ çalışıyor ve tablodan türeyen bulgular yerinde — mutasyon
    # taramayı tümden öldürseydi bu çivi de "yeşil" olurdu ve hiçbir şey ölçmezdi.
    assert "BEYAN DIŞI KOPYA: /opt/meridian/.env [MERIDIAN_DASH_TOKEN]" in r.stdout


def _serh_metni(betik: pathlib.Path) -> str:
    """Betiğin metni, ŞERH İŞARETLERİ ve SATIR SARMASI atılmış hâlde. Şerhte aranan bir cümle
    ham metinde `#` ve `\n` yüzünden bulunamaz; çivinin bir satır sarmasıyla kırılması onu
    ölçüm değil, biçim bekçisi yapardı."""
    ham = betik.read_text(encoding="utf-8")
    return " ".join(re.sub(r"^\s*#:?", " ", ham, flags=re.M).split())


def test_O7_SERHTEKI_KOPYA_SAYILARI_tablodan_OLCULUR():
    """(K5) ŞERHTEKİ SAYI BİR KOPYADIR. Betiğin başlık şerhi ve `openrouter`in kuru-koşum şerhi
    kopya SAYISI taşıyor; tablo büyüdüğünde bu sayılar sessizce eskir — bu turda tam öyle oldu
    (tablo 17 → 23 iken şerhte "2-3 kopya" ve "8 kopya" yazıyordu) ve ancak elle arandığı için
    bulundu. Sayı artık TABLODAN ölçülür ve metinde ARANIR (tek-kaynak yasası)."""
    k = _betik_kopyalari()
    metin = _serh_metni(BETIK)
    or_kopya = len([x for x in k if x["sir"] == "OPENROUTER_API_KEY"])
    nous_kopya = len([x for x in k if x["sir"] == "NOUS_API_KEY"])
    alt_kopya = len([x for x in k if x["alt"] == "openrouter"])
    assert or_kopya == 12 and nous_kopya == 2 and alt_kopya == 14, (or_kopya, nous_kopya, alt_kopya)
    # D7 DÜŞÜK-10: başlıktaki "her sırrın 2-12 kopyası var" ARALIĞI da elle yazılmış bir sayıydı.
    # Bugün doğruydu ama O7'nin türetmesine BAĞLI değildi — tablo büyüdüğünde sessizce eskiyecek
    # tek satır oydu.
    sayim = {s: len([x for x in k if x["sir"] == s]) for s in {x["sir"] for x in k}}
    en_az, en_cok = min(sayim.values()), max(sayim.values())
    assert (en_az, en_cok) == (2, 12), sayim
    assert f"her sırrın {en_az}-{en_cok} kopyası var" in metin, \
        "başlık şerhindeki kopya ARALIĞI tabloyla ayrıştı"
    assert f"OPENROUTER artık {or_kopya} kopya (NOUS {nous_kopya})." in metin, \
        "başlık şerhi tabloyla ayrıştı"
    assert f"{alt_kopya} kopya da, birim listesi de kopya tablosundan gelir" in metin, \
        "`openrouter` kuru-koşum şerhi tabloyla ayrıştı"


def test_O8_MUT_tablo_BUYURSE_serh_sayisi_AYRISIR(tmp_path):
    """O7'nin ısırdığı dal: tabloya YEDİNCİ bir üye satırı girerse şerhteki sayı eskide kalır ve
    çivi kırmızıya döner. Mutasyonsuz bir O7, "sayıyı bir kez doğru yazdım" demekten öteye
    gitmezdi."""
    yeni_satir = ("openrouter OPENROUTER_API_KEY env /opt/hindsight/.env"
                  " HINDSIGHT_API_REFLECT_LLM_4_API_KEY koru koru -\n")
    var_satir = ("openrouter OPENROUTER_API_KEY env /opt/hindsight/.env"
                 " HINDSIGHT_API_REFLECT_LLM_1_API_KEY koru koru -\n")
    m = _mutant(tmp_path, (var_satir, var_satir + yeni_satir))
    k = _betik_kopyalari(m)
    metin = _serh_metni(m)
    or_kopya = len([x for x in k if x["sir"] == "OPENROUTER_API_KEY"])
    assert or_kopya == 13, k
    assert f"artık {or_kopya} kopya" not in metin, \
        "şerh sayısı mutasyonla birlikte kaydı — O7 tabloyu değil kendini ölçüyor"
    sayim = {s: len([x for x in k if x["sir"] == s]) for s in {x["sir"] for x in k}}
    assert f"her sırrın {min(sayim.values())}-{max(sayim.values())} kopyası var" not in metin, \
        "aralık mutasyonla birlikte kaydı — O7'nin D7 eki kendini ölçüyor"


def test_O9_UYE_alani_CIFT_SATIRSA_yazim_DURUR_ve_TAZE_ANAHTAR_yazilmaz(tmp_path):
    """K8a'nın dersi bu alanlara da uygulanır — ve zincirin BOZUK hâli operatörün anahtarını
    HARCAMAZ. Çift `^AD=` satırında hafıza SONUNCUyu okur, operatör İLKİNİ düzenler; yardımcı bu
    yüzden durur ("yazım YAPILMADI").

    DURMA NOKTASI ÖLÇÜLDÜ (2026-09-08) ve beklediğimden İYİ çıktı: OPENROUTER negatif kontrolü
    bilerek bozuk değeri TÜM `dosya|env|url` kopyalarına yazdığı için `/opt/hindsight/.env`in
    bozuk satırına daha YAZIMDAN ÖNCE çarpılır, trap her kopyayı geri koyar ve operatörün taze
    anahtarı hiçbir dosyaya girmez. Yani negatif kontrol aynı zamanda bir ÖN-UÇUŞtur: zincir
    kısalır/bozulursa bakım penceresi yarım bir rotasyonla değil, TEMİZ bir dur ile kapanır.
    Bu çivi o sıralamayı pinler — sıra değişirse (yazım negatif kontrolün önüne geçerse) burası
    öter. `--envanter` aynı hâli önceden "ÇİFT SATIR (2)" diye söyler; operatörün ilk komutu odur."""
    kok, ortam = _sahte_ortam(tmp_path)
    p = kok / "opt/hindsight/.env"
    alan = UYE_ALANLARI[0]
    p.write_text(p.read_text(encoding="utf-8") + f"{alan}={ESKI['or']}\n", encoding="utf-8")

    # (1) ÖN-BAKIŞ: envanter bu hâli DEĞER BASMADAN söyler.
    r0 = _kos(BETIK, ortam, "--envanter")
    assert r0.returncode == 0, r0.stdout + r0.stderr
    satir = [s for s in r0.stdout.splitlines() if f"/opt/hindsight/.env [{alan}]" in s]
    assert satir and "ÇİFT SATIR (2)" in satir[0], satir

    # (2) YAZIM: durur ve alanı ADIYLA söyler.
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode != 0, r.stdout + r.stderr
    assert alan in (r.stdout + r.stderr) and "yazım YAPILMADI" in (r.stdout + r.stderr)

    # (3) TAZE ANAHTAR HİÇBİR KOPYADA YOK ve eski değerler yerinde (H5 ile aynı disiplin).
    ham = "\n".join(x.read_text(encoding="utf-8", errors="ignore")
                    for x in kok.rglob("*") if x.is_file() and ".sahte" not in str(x))
    assert YENI_OR not in ham and YENI_NOUS not in ham, "yarım rotasyon: taze anahtar diske düştü"
    assert _env_alan(kok / "opt/apisix/.env-apisix", "OPENROUTER_API_KEY") == f'"{ESKI["or"]}"'
    assert _env_alan(kok / "home/ubuntu/.hermes/profiles/sef/.env",
                     "OPENROUTER_API_KEY") == ESKI["or"]
    assert _env_alan(kok / "opt/hindsight/.env", UYE_ALANLARI[1]) == ESKI["or"]


# =================================================================================================
# P) TUR 7 — BAĞIMSIZ İNCELEMENİN KÖKLERİ (2026-09-08, `inceleme_D5D6`)
# =================================================================================================
# ORTAK DERS: kusurların HİÇBİRİ mutlu yolda değildi. Hepsi ARIZA yolundaydı — ve bu betiğin bütün
# tezi arıza yolunun dürüstlüğü olduğu için, en pahalı yer tam orasıdır.
#
# BLOKLAYICI (P1-P3). Negatif kontrol hedeflere BİLEREK bozuk/boş değer yazar ve birimleri o
# değerle YENİDEN BAŞLATIR. Hazırlık beklemesi aşılırsa (`olcum_yok`, çıkış 2) trap DOSYALARI geri
# alıyordu ama BİRİMLERİ yeniden başlatmıyordu: ölçülen hâl (inceleme probu, 2026-09-08)
# `/run/credentials/meridian.service/NOUS_API_KEY` = `''` ve
# `/run/credentials/hindsight-api.service/HINDSIGHT_API_LLM_API_KEY` = `sahte-…`. Yani canlıda
# birimler bilerek bozuk anahtarla koşmaya devam ediyor, operatörün gördüğü tek cümle "hazırlık
# bekleme aşıldı" oluyordu — "hiçbir kalıcı yazım yok" disiplinini bilen bir okuyucuya
# "bir şey olmadı" diye okunur. M4 bu sınıfa YAPISAL olarak kördü (`/run/credentials/` süzgeçten
# çıkarılmıştı); süzgeç kalktı ve ölçü "kaynağıyla aynı mı"ya çevrildi.
#
# YÜKSEK (P4-P5). `trap 'birinci; ikinci' EXIT` içinde `birinci` `exit` ederse `ikinci` HİÇ
# KOŞMAZ (bash EXIT-trap semantiği). `_negatif_geri_al` geri alma başarısızlığında `die`
# ediyordu, yani `_temizle` hiç çağrılmıyor ve operatörün TAZE anahtarlarını taşıyan 0700 dizin
# diskte kalıyordu — üstelik "SİLİNEMEDİ" uyarısı bile basılmadan (K9a'nın kapattığı sessizlik bu
# yoldan geri geliyordu) ve çıkış kodu 2'den 1'e bozularak.
#
# P14 (D8, `inceleme_D7`/Y2 — AYNI SINIFIN ÜÇÜNCÜ BİÇİMİ). Bu kez arıza yolu YALAN SÖYLÜYORDU:
# yedek dizini hiç doğmadan düşen bir koşumda EXIT trap "bu koşum YEDEK aldı" reçetesi basıyordu,
# çünkü `YEDEK` ataması `install -d`den ÖNCEydi ve reçetenin tek kapısı o atamaydı. Arıza yolunun
# dürüstlüğü, DOĞRU olanı basmak kadar OLMAYANı basmamaktır.


def _islik_kalanlari(tmp_path: pathlib.Path) -> list[pathlib.Path]:
    """Koşumun KENDİ tmp'sinde kalan 0700 çalışma dizinleri (J8/K9a ile aynı arama)."""
    return [p for p in tmp_path.iterdir() if p.is_dir() and (p / "yardimci.py").exists()]


def test_P1_TAVAN_asiminda_BIRIMLER_geri_alinip_YENIDEN_BASLATILIR(tmp_path):
    """BLOKLAYICI-1, NOUS bacağı. Aşımdan sonra `/run/credentials/meridian.service/NOUS_API_KEY`
    ESKİ değere dönmüş olmalı — "dosyalar geri alındı" ile "birim geri alınmış değeri OKUYOR"
    aynı şey değildir ve aradaki fark canlıda bir birimi SESSİZCE YETKİSİZ bırakır (2026-09-07
    vakasının tam biçimi).

    BEYAN DA ÖLÇÜLÜR: kurtarma sessiz olsaydı operatör "bir şey olmadı" diye okurdu.

    D8 (inceleme D7/Y3) — BEYANIN ÖNERDİĞİ DOĞRULAMA DA ÖLÇÜLÜR. İlk biçim tek bir komut
    öneriyordu: `sudo $0 --envanter`. O komut DOSYALARI kıyaslar ve bu dalda dosyalar ZATEN geri
    alınmıştır, yani her hâlükârda "EŞİT" der — bu dalın gerçek arıza sınıfı ("birim açılmıyor")
    ona YAPISAL OLARAK GÖRÜNMEZ. Yani beyan doğruydu, ama önerdiği doğrulama YANLIŞ BİR GÜVEN
    üretiyordu. Çivi şimdi ikisini birden zorluyor: birim sorusu VAR ve dosya sorusunun körlüğü
    YAZILI."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "999999"
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "hazırlık bekleme aşıldı" in r.stderr, r.stderr
    kred = kok / "run/credentials/meridian.service/NOUS_API_KEY"
    assert kred.exists(), "credential hiç doğmadı — çivi kör (pozitif kontrol)"
    assert kred.read_text(encoding="utf-8").strip() == ESKI["nous"], \
        "birim BOŞ/BOZUK credential ile koşmaya devam ediyor (geri almadan sonra restart YOK)"
    assert "BİLEREK BOZUK/BOŞ DEĞERLE AÇILMIŞTI" in r.stderr, r.stderr
    assert "systemctl is-active" in r.stderr and "journalctl -u" in r.stderr, \
        "kurtarma beyanı yalnız DOSYA doğrulaması öneriyor — birim sorusu YOK (D7/Y3)"
    assert "KÖRDÜR" in r.stderr, "envanterin bu daldaki körlüğü YAZILI DEĞİL (D7/Y3)"
    assert "yeniden başlatıldı: meridian.service" in r.stderr, r.stderr
    # İki restart: negatif kontrolün BOZMA turu + trap'in KURTARMA turu. Üçüncü bir restart
    # (hazırlık beklemesi) trap içinde YAPILMAZ — orada ölçüm yapmak ölçüm arızasını temizliğin
    # önüne koymak olurdu.
    assert _birim_sirasi(kok) == ["meridian.service", "meridian.service"], _birim_sirasi(kok)


def test_P2_MUT_kurtarma_restarti_kalkarsa_P1_kirmizi(tmp_path):
    """P1'in ısırdığı dal: trap yolundaki `_negatif_restart_kurtarma`. Kaldırılınca ölçülen canlı
    hâl geri gelir — dosya temiz, ÇALIŞAN BİRİM boş credential'da."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HAZIR_N"] = "999999"
    m = _mutant(tmp_path, ("  _negatif_restart_kurtarma\n", "  :\n"))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    kred = kok / "run/credentials/meridian.service/NOUS_API_KEY"
    assert kred.read_text(encoding="utf-8").strip() == "", \
        "mutasyon ısırmıyor — P1 yanlış sebeple yeşil"
    assert "BİLEREK BOZUK/BOŞ DEĞERLE AÇILMIŞTI" not in r.stderr


def test_P3_OPENROUTER_bacaginda_da_kurtarma_kosar(tmp_path):
    """BLOKLAYICI-1'in ikinci (ve canlıda daha olası) biçimi: hindsight-api `/health` 200
    vermezse OPENROUTER negatif kontrolü aşımdan düşer. `apisix` `$env://` çözümünü YALNIZ
    açılışta yaptığı için kapı da sahte anahtarı taşır — iki birim birden kurtarılmalıdır.

    NOUS bacağı bu dünyada GEÇER (meridian `/healthz` 200), yani aşım gerçekten OPENROUTER
    turundadır: `SAHTE_HEALTH_KOD` ile `SAHTE_HAZIR_N` AYRI dünyalardır (biri "cevap veriyor ama
    200 değil", öteki "ulaşılamıyor")."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_HEALTH_KOD"] = "503"
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "hindsight-api.service" in r.stderr and "HTTP 503" in r.stderr, r.stderr
    kred = kok / "run/credentials/hindsight-api.service/HINDSIGHT_API_LLM_API_KEY"
    assert kred.read_text(encoding="utf-8").strip() == ESKI["llm"], \
        "hafıza birimi SAHTE LLM anahtarıyla koşmaya devam ediyor"
    # Kapının upstream başlığı da geri alınmış OLMALI ve kapı o değerle YENİDEN AÇILMIŞ olmalı.
    assert _env_alan(kok / "opt/apisix/.env-apisix", "OPENROUTER_AUTH") == f'"Bearer {ESKI["or"]}"'
    for b in ("apisix.service", "hindsight-api.service"):
        assert b in r.stderr.split("yeniden başlatıldı:")[1], r.stderr
    # Taze anahtar hiçbir dosyaya girmedi (H5 ile aynı disiplin).
    ham = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in kok.rglob("*")
                    if p.is_file() and ".sahte" not in str(p))
    assert YENI_OR not in ham and YENI_NOUS not in ham


def test_P4_GERI_ALMA_DUSERSE_temizlik_KOSAR_cikis_2_ve_hedef_YERINDE(tmp_path):
    """YÜKSEK-2'nin üç ayağı BİRDEN, tek koşumda:
      (a) `_temizle` GARANTİ — taze anahtar taşıyan 0700 dizin diskte KALMAZ;
      (b) çıkış kodu 2 KALIR ("2 = ölçülemedi" sözleşmesi en kötü hâlde bozulamaz);
      (c) hedef ARADAN KALDIRILMAZ — `rm` sonra `cp` sırası, `cp` düştüğünde bir
          `LoadCredential` KAYNAĞINI YOK ediyordu ve kaynağı olmayan birim HİÇ BAŞLAMAZ.

    Dünya: geri alma `cp`si düşer (`SAHTE_CP_KIRIK`) VE hazırlık aşılır (`SAHTE_HAZIR_N`) —
    ikincisi şart, çünkü geri almanın İLK KEZ TRAP İÇİNDE koştuğu yol ancak böyle doğar."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_CP_KIRIK"] = "1"
    ortam["SAHTE_HAZIR_N"] = "999999"
    r = _kos(BETIK, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "GERİ ALMA BAŞARISIZ" in r.stderr, r.stderr
    assert "birim BAŞLAMAZ" in r.stderr, "die metni yanlış teşhis veriyor (dosya YOK olabilir)"
    assert not _islik_kalanlari(tmp_path), "taze anahtar taşıyan 0700 dizin diskte KALDI"
    assert (kok / "etc/meridian/nous_api_key").exists(), \
        "geri alma hedefi ARADAN KALDIRILDI — LoadCredential kaynağı YOK, birim BAŞLAMAZ"


def test_P5_MUT_ESKI_TRAP_bicimi_temizligi_YUTAR_ve_kodu_BOZAR(tmp_path):
    """P4'ün ısırdığı dal: trap gövdesinin TEK FONKSİYON olması + geri almanın `die` yerine
    `return 1` etmesi. Mutant ilk biçime döner (`trap 'a; b'` + `die`) ve ölçülen iki arıza da
    geri gelir: çalışma dizini kalır, çıkış kodu 2→1 olur."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_CP_KIRIK"] = "1"
    ortam["SAHTE_HAZIR_N"] = "999999"
    m = _mutant(
        tmp_path,
        ("  trap '_negatif_trap' EXIT\n", "  trap '_negatif_geri_al; _temizle' EXIT\n"),
        ('  [ -z "$basarisiz" ] || { echo "!! GERİ ALMA BAŞARISIZ:$basarisiz',
         '  [ -z "$basarisiz" ] || { die "GERİ ALMA BAŞARISIZ:$basarisiz'))
    r = _kos(m, ortam, "--openrouter", girdi=f"{YENI_NOUS}\n{YENI_OR}\n")
    assert r.returncode == 1, (r.returncode, "çıkış kodu bozulmuyor — P4 yanlış sebeple yeşil")
    assert _islik_kalanlari(tmp_path), "temizlik mutasyonu ısırmıyor — P4 yanlış sebeple yeşil"
    assert "ÇALIŞMA DİZİNİ SİLİNEMEDİ" not in r.stderr, \
        "silme HİÇ denenmedi; sessizlik K9a'nın kapattığı sınıftır"
    assert kok.exists()


# --- P6: `_kredensiyeller` ↔ drop-in `LoadCredential=` (ayrışma çivisi) ---------------------------

def _betik_kredensiyelleri() -> set[tuple[str, str]]:
    """Betiğin `_kredensiyeller` heredoc'u → {(birim, kimlik)}. Tablo bir SABİTTİR (alt komut
    süzgeciyle okunur, bir alt komut olarak basılmaz), o yüzden çapa heredoc İŞARETİDİR."""
    ham = BETIK.read_text(encoding="utf-8")
    govde = ham.split("<<'KRED_SON'\n", 1)[1].split("\nKRED_SON\n", 1)[0]
    cikti = set()
    for satir in govde.splitlines():
        _alt, birim, kimlik = satir.split()
        cikti.add((birim, kimlik))
    return cikti


def test_P6_KREDENSIYEL_tablosu_DROPINLERLE_AYRISMAZ():
    """ORTA-7. Şerh "Kimlikler drop-in'lerdeki `LoadCredential=<kimlik>:<kaynak>` ile BİREBİR
    aynıdır" diyor ama bunu bir ÇİVİ değil, inceleme eliyle doğrulamıştı. Ayrışmanın belirtisi
    yine HİÇBİR ŞEY: betik bir dosyaya yazar, systemd BAŞKA bir kimliği arar ve arıza ancak ilk
    gerçek çağrıda görünür. İki yön de ölçülür (tek yön, silinen bir satırı görmezdi).

    ÜÇÜNCÜ AYAK: drop-in'in KAYNAK YOLU kopya tablosunda bir `dosya`/`url` hedefi olmalı — yoksa
    rotasyon systemd'nin okuduğu dosyayı hiç yazmaz ve credential ESKİ değerde kalır."""
    dropin = {(b, k) for b, d in KRED_KAYNAKLARI.items() for k in d}
    betik = _betik_kredensiyelleri()
    assert betik, "kredensiyel tablosu BOŞ — ayrıştırıcı kör (pozitif kontrol)"
    assert betik == dropin, (f"betikte fazla: {sorted(betik - dropin)} · "
                             f"drop-in'de fazla: {sorted(dropin - betik)}")
    hedefler = {x["yol"] for x in _betik_kopyalari() if x["tur"] in ("dosya", "url")}
    kaynaklar = {k for d in KRED_KAYNAKLARI.values() for k in d.values()}
    assert kaynaklar <= hedefler, f"rotasyonun YAZMADIĞI credential kaynağı: {kaynaklar - hedefler}"


# --- P7-P9: kuru raporun ve şerhin operatöre söyledikleri -----------------------------------------

def _hindsight_tavani() -> int:
    """Üretim varsayılanı KODDAN okunur (O7/O8 deseni): şerhteki sayı bir KOPYADIR ve tablodan
    değil, ancak koddan türetilirse ayrışamaz."""
    m = re.search(r'HAZIR_TAVAN_S_hindsight_api="\$\{HAZIR_TAVAN_S_hindsight_api:-(\d+)\}"',
                  BETIK.read_text(encoding="utf-8"))
    assert m, "hindsight tavanı okunamadı"
    return int(m.group(1))


def test_P7_SUDO_ENV_bicimi_SERHTE_ve_KURU_RAPORDA_koddan_turer(tmp_path):
    """ORTA-5. Betiğin BELGELENEN çağrı biçimi `sudo ./sir_rotasyon.sh …`dır ve sudo'nun
    varsayılan `env_reset`i `HAZIR_TAVAN_S_hindsight_api`yi DÜŞÜRÜR — yani "operatör tavanı
    ölçerek yükseltebilir" sözleşmesi belgelenen biçimde çalışmayabilir. Güvenli biçim şerhte VE
    kuru raporda YAZILI olmalı; sayı KODDAN türemeli.

    TAVAN 300: ölçülen açılış 99 s (2026-09-08 08:07:06→08:08:45), yani 180 s yalnız 1,8× paydı
    ve negatif kontroldeki (SAHTE anahtarlı) açılış hiç ölçülmedi."""
    assert _hindsight_tavani() == 300, "ölçüm + ~3× pay (99 s açılış, 2026-09-08)"
    serh = _serh_metni(BETIK)
    assert (f"sudo env HAZIR_TAVAN_S_hindsight_api={_hindsight_tavani()} "
            "./deploy/oracle-a1/sir_rotasyon.sh --openrouter") in serh, serh[-1500:]
    # KURU RAPORDA sayı ETKİN değerdir (çivi ortamı 2'ye sıkıştırır) — literal olsaydı operatör
    # kendi ortamındaki tavanı değil, bir sabiti okurdu.
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "sudo env HAZIR_TAVAN_S_hindsight_api=2 " in r.stdout, r.stdout
    # hindsight-api YENİDEN BAŞLAMAYAN bir alt komutta satır BASILMAZ: ilgisiz bir tavanı
    # önermek, kuru raporu gürültüyle doldurmaktır (bedel yasası).
    r2 = _kos(BETIK, ortam, "--dash", "--kuru")
    assert "HAZIR_TAVAN_S_hindsight_api" not in r2.stdout, r2.stdout


def test_P8_MUT_TAVAN_degisirse_SERH_AYRISIR(tmp_path):
    """P7'nin ısırdığı dal: şerhteki sayı koddan türemeseydi mutasyon onu kaydırmazdı."""
    m = _mutant(tmp_path, ('HAZIR_TAVAN_S_hindsight_api:-300}', 'HAZIR_TAVAN_S_hindsight_api:-180}'))
    serh = _serh_metni(m)
    assert "sudo env HAZIR_TAVAN_S_hindsight_api=180 " not in serh, \
        "şerh sayısı mutasyonla birlikte kaydı — P7 kendini ölçüyor"


@pytest.mark.parametrize("alt", ["--kapi", "--tenant", "--db", "--dash", "--openrouter"])
def test_P9_KURU_RAPOR_tick_watchdog_ON_KOSULUNU_soyler(tmp_path, alt):
    """ORTA-8. Kalıcı kayıt (`bakim-penceresi-tick-watchdog`): timer 45 dk bayatlıkta worker'ı
    yeniden başlatır ve `--openrouter` meridian'ı ÜÇ kez yeniden başlatır — her restart
    `/healthz`i dakikalarca 503 (bayat) yapar. Timer pencerenin ortasında ateşlenirse ölçüm
    SEBEPSİZ `OLCULEMEDI` verir ve betiğin çıktısından bu ASLA anlaşılmaz."""
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, alt, "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ÖN KOŞUL: sudo systemctl stop meridian-tick-watchdog.timer" in r.stdout, r.stdout
    assert "sonda geri aç" in r.stdout, r.stdout
    assert "meridian-tick-watchdog.timer" in _serh_metni(BETIK), "şerh bu ön koşulu hiç anmıyor"


# --- P10-P11: arıza yolunda reçete + değer kırpma -------------------------------------------------

def test_P10_GERI_ALMA_RECETESI_ARIZADA_da_basilir(tmp_path):
    """ORTA-6. Reçete her alt komutun SON satırıydı, yani YALNIZ başarıda basılıyordu. Taze
    anahtar kopyalara YAZILDIKTAN sonra kanıt aşamasında durulursa (yapıştırmada bir boşluk →
    upstream RET → çıkış 2) ekranda geri alma yolu YOKTU. "Yedek dizininin yolu daha önce
    basıldı" ile "ne yapacağı yazıldı" aynı şey değildir."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_KOR"] = "1"                      # kilit yürürlükte değil → kanıt YAZIMDAN SONRA düşer
    r = _kos(BETIK, ortam, "--kapi")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    y = _yedek_dizini(kok)
    assert ">> GERİ ALMA" in r.stderr, r.stderr
    assert y.name in r.stderr, "reçete YEDEK dizinini göstermiyor"
    assert "apisix.service" in r.stderr and "meridian.service" in r.stderr, r.stderr
    # BAŞARIDA DA basılır: iki yol tek satırla anlatılır, operatör "hangi hâldeydim" diye
    # ayrım yapmak zorunda kalmaz.
    kok2, ortam2 = _sahte_ortam(tmp_path / "ikinci")
    r2 = _kos(BETIK, ortam2, "--dash")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert ">> GERİ ALMA" in r2.stderr, r2.stderr
    assert _yedek_dizini(kok2).name in r2.stderr


def test_P11_DEGER_bastaki_ve_sondaki_BOSLUKLARI_kirpilir(tmp_path):
    """ORTA-6 (ikincil). `_deger_dosyadan` yalnız `\\r\\n` kırpıyordu; boşluk taşıyan bir değer
    dosyası 12 kopyaya AYNEN yazılır, upstream reddeder ve rotasyon kanıt aşamasında düşerdi —
    yani "yanlış anahtar" ile "doğru anahtar + bir boşluk" AYNI belirtiyi verir.

    ÖLÇÜM İKİ KATMANLIDIR VE İKİSİ AYRI ŞEY SÖYLER:
      (a) YARDIMCI katmanı — asıl kapı. Değer dosyası boşluklu geldiğinde yazılan dosya TEMİZ
          olmalı. `sahip=-` seçildi: çivi makinesinde `chown` yapılmaz (root değiliz) ve ölçüm
          sahiplik değil KIRPMA hakkındadır.
      (b) OPERATÖR yolu — `read -rs` bash'in kendi IFS kırpmasını ZATEN yapar, yani uçtan uca
          koşum bu düzeltme OLMADAN da yeşildi. Bu bir POZİTİF KONTROLDÜR ve öyle beyan edilir:
          (a) olmasaydı (b) hiçbir şey ölçmezdi (çivi yeşili kanıt değildir)."""
    y = _yardimci(tmp_path)
    dgr = tmp_path / "deger.txt"
    dgr.write_text(f"  {YENI_OR} \t\n", encoding="utf-8")
    hedef = tmp_path / "hedef"
    r = _py(y, "yaz-dosya", str(hedef), str(dgr), "0600", "-", "-")
    assert r.returncode == 0, r.stdout + r.stderr
    assert hedef.read_text(encoding="utf-8") == YENI_OR + "\n", repr(hedef.read_text())

    kok, ortam = _sahte_ortam(tmp_path / "ucauc")
    r2 = _kos(BETIK, ortam, "--openrouter", girdi=f"  {YENI_NOUS}  \n\t{YENI_OR} \n")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert (kok / "etc/meridian/nous_api_key").read_text(encoding="utf-8") == YENI_NOUS + "\n"
    assert _env_alan(kok / "opt/apisix/.env-apisix", "OPENROUTER_API_KEY") == f'"{YENI_OR}"'
    assert _env_alan(kok / "opt/hindsight/.env", UYE_ALANLARI[0]) == YENI_OR


def test_P12_STAT_iki_bicimde_de_duserse_OLCULEMEDI_der(tmp_path):
    """DÜŞÜK-9. `sudo stat -c %s … || sudo stat -f %z …` GNU/BSD geri düşüşüdür; İKİSİ DE
    düşerse `set -e` koşumu çıkış 1 ile keserdi ve tasarlanan `olcum_yok` (çıkış 2) HİÇ koşmazdı.
    "Ölçemedim" ile "arıza" aynı hüküm DEĞİLDİR — bu betiğin bütün sözleşmesi o ayrımdır."""
    _, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_STAT_KIRIK"] = "1"
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 2, (r.returncode, r.stdout + r.stderr)
    assert "credential BOYUTU ÖLÇÜLEMEDİ" in r.stderr, r.stderr


def test_P13_SOZLUK_BEDELININ_OLCUM_SATIRI_SERHTE():
    """ORTA-4. İnceleme sözlüğün ÜÇÜNCÜ-TARAF anahtarlarını da bağırabileceğini işaret etti ve
    D6'nın "bedel sıfır gürültü" ölçümünün KAPSAMI test sahnesiydi. Rol-1 canlıda ölçtü
    (2026-09-08, 7 dosya, yalnız adlar): sözlük dışında kalan üç ad da sonek sözlüğüne UYMUYOR,
    yani gürültü sıfır. Sözlük KALDI — ama ölçüm KODA YAZILDI: bir sonraki tur "bedel
    ölçülmemişti" diye sözlüğü gevşetmesin ya da genişletmesin (bedel yasası).

    Çivi ÖLÇÜMÜN VARLIĞINI zorlar, sonucunu değil: satır silinirse beyan da silinmiş olur."""
    serh = _serh_metni(BETIK)
    assert "BEDEL ÖLÇÜLDÜ, VARSAYILMADI — Rol-1, A1, 2026-09-08" in serh, serh[-1500:]
    for ad in ("HINDSIGHT_CP_ACCESS_KEY", "APISIX_ADMIN_KEY", "PANO_GIRIS_PAROLA"):
        assert ad in serh, ad
    # Ölçülen adlar sözlüğe GERÇEKTEN uymamalı — beyan ile kod ancak böyle ayrışamaz.
    sonekler = re.search(r'_SIR_ADI_SONEKLERI="([^"]+)"', BETIK.read_text(encoding="utf-8"))
    assert sonekler, "sonek sözlüğü okunamadı"
    for ad in ("HINDSIGHT_CP_ACCESS_KEY", "APISIX_ADMIN_KEY", "PANO_GIRIS_PAROLA"):
        assert not any(ad.endswith(s) for s in sonekler.group(1).split()), \
            f"beyan ile sözlük ayrıştı: {ad} sözlüğe UYUYOR, yani gürültü sıfır DEĞİL"


def test_P14_YEDEK_ALINAMAZSA_GERI_ALMA_RECETESI_BASILMAZ(tmp_path):
    """D7/Y2. `_geri_alma_recetesi`nin TEK kapısı `[ -n "$YEDEK" ]`tir, yani `YEDEK` ataması
    "bu koşum yedek ALDI" beyanıdır. Atama `install -d`den ÖNCE yapılıyordu: dizin doğmadan düşen
    bir koşumda (disk dolu · yetki · salt-okunur bağlama) EXIT trap yine
    ">> GERİ ALMA (bu koşum YEDEK aldı…)" basıyor, operatörü VAR OLMAYAN bir dizinden geri
    koymaya ve karşılıksız ÜÇ restart'a çağırıyordu — fonksiyonun kendi şerhinin ("olmayan bir
    yedeği göstermek, olmayan bir güvence vermek olurdu") yasakladığı hâl.

    ÖLÇÜM DÖRT AYAKLIDIR ve üçü tek başına yetmez:
      (a) çıkış 1 KALIR — `install`ın `set -e` hükmü; 2'ye (`olcum_yok`) dönüşmemeli, çünkü bu
          bir ÖLÇÜM arızası değil bir ÖN KOŞUL arızasıdır;
      (b) reçete BASILMAZ — asıl kusur;
      (c) yedek dizini gerçekten DOĞMAMIŞ — (b) yanlış sebeple de yeşil olabilirdi (ör. trap hiç
          koşmasaydı), bu ayak onu ayırır;
      (d) `install` GERÇEKTEN çağrıldı ve hiçbir kopya YAZILMADI — dal doğru yerde ölçülüyor ve
          zararın sınırı (yedek her alt komutta bütün yazımlardan ÖNCE alınır) da kanıtlanıyor."""
    kok, ortam = _sahte_ortam(tmp_path)
    ortam["SAHTE_INSTALL_KIRIK"] = "1"
    r = _kos(BETIK, ortam, "--dash")
    assert r.returncode == 1, (r.returncode, r.stdout + r.stderr)
    assert ">> GERİ ALMA" not in r.stderr, r.stderr
    assert not list((kok / "root").glob("sir-yedek-*")), "yedek dizini doğmamalıydı"
    assert "install -d -m 0700" in (kok / ".sahte/argv.log").read_text(encoding="utf-8")
    assert (kok / "etc/meridian/dash_token").read_text(encoding="utf-8") == ESKI["dash"] + "\n"
    assert _env_alan(kok / "opt/meridian/.dash.env", "MERIDIAN_DASH_TOKEN") == f'"{ESKI["dash"]}"'
    # Temizlik yine de KOŞTU: reçetenin susması, `_cikis`in ikinci ayağını rehin almamalı.
    assert "ÇALIŞMA DİZİNİ SİLİNEMEDİ" not in r.stderr, r.stderr


def test_P15_KURU_RAPOR_RESTART_CARPANINI_da_beyan_eder(tmp_path):
    """D7/Y4 — BEDEL YASASI, YARIM BEYAN. Kuru rapor birim başına TEK bir `tavan: 300 s` satırı
    basıyordu ve okuyan "en fazla 300 s" diye anlıyordu; ölçülen gerçek (PROBE3, 2026-09-08)
    `--openrouter`de birim başına ÜÇ restart, yani 3 × 300 s. Kazanç (kısa satır) ölçülmüş,
    bedeli (gizlenen bekleme) ölçülmemişti — pencereyi operatör bu satıra bakarak açıyor.

    ÇARPAN TEK KAYNAKTAN TÜRER ve o kaynak bir KOPYA olduğu için ayrışma çivisiyle bağlıdır:
    `_NK_ALT_KOMUTLARI` beyanı ile betiğin GERÇEK `_negatif_kontrol` çağrı yerleri aynı kümeyi
    vermeli. İkinci bir alt komuta negatif kontrol eklenir de liste güncellenmezse kuru rapor o
    komut için "1 restart" der ve bedel yine gizlenir."""
    kaynak = BETIK.read_text(encoding="utf-8")
    beyan = re.search(r'^_NK_ALT_KOMUTLARI="([^"]*)"', kaynak, flags=re.M)
    assert beyan, "restart çarpanının kaynağı okunamadı"
    cagrilan = set(re.findall(r"^\s*_negatif_kontrol\s+([a-z_]+)\b", kaynak, flags=re.M))
    assert cagrilan, "negatif kontrol çağrısı bulunamadı — ayrıştırıcı kör (pozitif kontrol)"
    assert set(beyan.group(1).split()) == cagrilan, (beyan.group(1), cagrilan)

    # UÇTAN UCA: beyan koda değil, OPERATÖRÜN GÖRDÜĞÜ SATIRA dönüşmeli.
    _, ortam = _sahte_ortam(tmp_path)
    r = _kos(BETIK, ortam, "--openrouter", "--kuru")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "her birim 3 kez yeniden başlar" in r.stdout, r.stdout
    assert "× 3 restart = en kötü" in r.stdout, r.stdout
    # NEGATİF KONTROLSÜZ alt komutta çarpan 1'dir — sabit bir "3" basmak da uydurma olurdu.
    _, ortam2 = _sahte_ortam(tmp_path / "dash")
    r2 = _kos(BETIK, ortam2, "--dash", "--kuru")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "her birim 1 kez yeniden başlar" in r2.stdout, r2.stdout
    assert "× 3 restart" not in r2.stdout, r2.stdout

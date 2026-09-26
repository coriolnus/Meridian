"""test_dash_token_betigi_v559.py — TSK-064: `deploy/oracle-a1/dash_token_credential.sh` pano jetonunu curl
ARGV'sine koymaz ve YENİ jetonu HİÇBİR çıktıya basmaz (2026-09-26).

NUMARA: `ls tests | grep -E '_v55[89]|_v56'` boş (ana checkout + on bir worktree tarandı 2026-09-26; en
yüksek v557). Numara Rol-1 brief'inden.

BULGU (TSK-226b sınıf taraması — `tests/test_cp_rotasyon_v556.py::SINIF_ISTISNALARI` kaydı, Rol-1 doğruladı):
  (a) `_auth_kodu` jetonu `curl -H "x-meridian-token: $1"` ile KOMUT SATIRINA koyuyordu — `ps` ve
      `/proc/<pid>/cmdline` onu makinedeki her kullanıcıya gösterir;
  (b) faz-1 sonu YENİ jetonu terminale — ve oradan ssh/ajan oturumunun dökümüne — basıyordu.
DÜZELTME: (a) başlık `curl -H @-` ile STDIN'den, `printf` bash YERLEŞİĞİ (süreç doğurmaz) — TSK-226b
`deploy/hermes_api.sh` deseni; (b) değer yerine YERİ (yol · ölçülen izin · sahip) ve operatörün KENDİ
terminalinde koşacağı OKUMA KOMUTU (metin, değer değil). Çıkış kodları ve faz akışı AYNI (C bölümü).

DÜZENEK. Betiğin KOPYASI tmp bir köke yönlendirilir: dört sabit (`BIRIM` `KRED` `ENVF` `API`) ve
`install -d … /etc/meridian` satırı, çapa sayısı pinli metin değişimiyle (sabitler betikten OKUNUR —
tek kaynak). PATH şimleri:
  · `sudo` geçirgen · `chown` no-op (olay günlüğüne yazar) · `install` `-o/-g`yi düşürür (root modellenmez);
  · `stat -c` ve `_token_oku`nun GNU `sed` ifadesi macOS için şimlenir (BSD sed `t;p`yi etiket sanır).
    GNU davranışı AYNEN: okunamayan dosyada `sed` çıkış 2 — D2 bu koda dayanır;
  · `systemctl` MODELDİR: `restart` anında ETKİN jetonu `meridian/api.py::_read_dash_token` sırasıyla
    hesaplar — 50 drop-in kuruluysa credential kaynağı (kaynak yoksa birim BAŞLAMAZ), 51 kurulu değilse
    `.dash.env`. `SAHTE_UYGULAMA=eski` yalnız ortamı okuyan eski uygulamayı, `sabit` jetonu yok sayan bir
    sunucuyu, `SAHTE_ACILMAZ=1` 50 kuruluyken açılmayan birimi modeller;
  · `curl` GERÇEKTİR: sahte pano 127.0.0.1:<rastgele>'de `/api/*` isteği ANINDA pytest sürecinin
    torunlarının argv görüntüsünü alır (v552 `_torunlar`, v556 G2 deseni) ve başlığı ETKİN jetonla yalnız
    bool olarak kıyaslar.

BÖLÜMLER
  A  statik — şim ön-koşulları · başlık stdin'den · jeton değişkeni hiçbir baskıya gitmez (kabuk
     sözcükleyicisi, pozitif/negatif kontrollü) · sınıf taraması (v556 `_sinif_tara`, tek kaynak)
  B  dinamik — ps (faz-1, faz-2) · çıktıda jeton yok · yer beyanı ÖLÇÜLEN izinle
  C  davranış — ESKİ biçimle BİREBİR: çıkış kodu · stdout/stderr · systemctl/chown olayları · dosya imzası ·
     sunucu istekleri (12 senaryo, üç dünya)
  D  bugünkü dünya (A1 2026-09-26 hâli: `.dash.env` YOK, `meridian.service.d`nin bütün drop-in'leri
     kurulu, `/etc/meridian/dash_token` Vault Agent render hedefi) — EMEKLİLİK KANITI (karar Rol-1'in).
     Bunlar bir ARIZAYI değil bugünkü DAVRANIŞI sabitler; betik değişirse ölçüm yeniden yapılır.
  M  mutasyonlar — her çivinin hedeflediği dalı ısırdığı (mutant tmp'de, özgün değişmez)

SIR DEĞERİ YOK: tohum jetonlar `SAHTE-` önekli; betiğin ürettiği jeton test kökünde yaşar. İddialar önce
bool/sayı/etikete indirgenir — süreç tablosu, ortam ya da değer hiçbir iddia mesajına girmez.
"""
from __future__ import annotations

import grp
import http.server
import os
import pathlib
import pwd
import re
import shutil
import stat
import subprocess
import sys
import threading

import pytest
import yaml

from tests.test_cp_rotasyon_v556 import _sinif_tara, _torun_argvleri_goruntusu

KOK_DEPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK_DEPO / "deploy" / "oracle-a1" / "dash_token_credential.sh"
DROPIN_DIZIN = KOK_DEPO / "deploy" / "oracle-a1" / "meridian.service.d"
ENVANTER = KOK_DEPO / "deploy" / "sir_envanteri.yaml"
AGENT_HCL = KOK_DEPO / "deploy" / "vault" / "agent.hcl"
SIR_ROTASYON = KOK_DEPO / "deploy" / "oracle-a1" / "sir_rotasyon.sh"

ESKI_ORTAM = "SAHTE-ESKI-ORTAM-JETONU-0559"   # tarihsel dünya: `.dash.env`teki jeton
ARA_JETON = "SAHTE-FAZ1-JETONU-0559"          # faz-1 sonrası dünya: iki kanal aynı değerde
KASA_JETON = "SAHTE-KASA-JETONU-0559"         # bugünkü dünya: Vault Agent'ın render ettiği değer
SABIT_JETON = "SAHTE-SUNUCU-SABIT-0559"       # `SAHTE_UYGULAMA=sabit`: sunucunun kabul ettiği tek değer
TOHUMLAR = {ESKI_ORTAM: "ESKI_ORTAM", ARA_JETON: "ARA_JETON", KASA_JETON: "KASA_JETON",
            SABIT_JETON: "SABIT"}
DAGINIK_ONEK = "MERIDIAN_DASH_TOKEN="
SED_IFADESI = "s/^MERIDIAN_DASH_TOKEN=//p;t;p"   # `_token_oku` — şim bu ifadeyi modeller (A0 pinler)


def _sabit(metin: str, ad: str) -> str:
    bulunan = re.findall(rf"^{ad}=(\S+)$", metin, re.M)
    assert len(bulunan) == 1, f"betik sabiti {ad}: {len(bulunan)} tanım"
    return bulunan[0]


def _kod(metin: str) -> str:
    """Tam-satır yorumlar atılmış metin (satır içi `#` tırnakta olabilir — dokunulmaz)."""
    return "\n".join(s for s in metin.splitlines() if not s.lstrip().startswith("#"))


# =================================================================================================
# ESKİ BİÇİM — bu dilimden ÖNCEKİ satırlar (e0e54f1c). Davranış eşitliği (C) ve mutasyonlar (M) bu
# tersine çevirmeyle kurulur. Her kalıp TAM BİR kez eşleşmeli (sayı pinli).
# =================================================================================================
AUTH_YENI = ("  printf 'x-meridian-token: %s\\n' \"$1\" \\\n"
             "    | curl -s -o /dev/null -w \"%{http_code}\" -H @- \"$API/api/hermes\" 2>/dev/null || echo 000\n")
AUTH_ESKI = ("  curl -s -o /dev/null -w \"%{http_code}\" -H \"x-meridian-token: $1\" \"$API/api/hermes\""
             " 2>/dev/null || echo 000\n")
IZIN_YENI_DESEN = r"(?m)^# --- dosyanın YERİ[^\n]*\n_izin\(\) \{[^\n]*\}\n\n"
KUYRUK_YENI_DESEN = r"(?ms)^  # YENİ TOKEN BASILMAZ.*?^  echo \"     sudo cat \$KRED\"\n"
KUYRUK_ESKI = "  echo \">> FAZ 1 TAMAM. YENİ TOKEN (panoya/CLI'ye gerekecek): $yeni\"\n"

ESKI_AUTH = ("sabit", AUTH_YENI, AUTH_ESKI)
ESKI_IZIN = ("desen", IZIN_YENI_DESEN, "")
ESKI_KUYRUK = ("desen", KUYRUK_YENI_DESEN, KUYRUK_ESKI)
ESKIYE = (ESKI_AUTH, ESKI_IZIN, ESKI_KUYRUK)


def _uygula(metin: str, degisimler) -> str:
    for tur, kaynak, hedef in degisimler:
        if tur == "sabit":
            assert metin.count(kaynak) == 1, f"çapa sayısı {metin.count(kaynak)} ≠ 1: {kaynak[:60]!r}"
            metin = metin.replace(kaynak, hedef)
        else:
            metin, adet = re.subn(kaynak, lambda _m: hedef, metin)
            assert adet == 1, f"desen sayısı {adet} ≠ 1: {kaynak[:60]!r}"
    return metin


def _eski_bicim(metin: str | None = None) -> str:
    return _uygula(BETIK.read_text(encoding="utf-8") if metin is None else metin, ESKIYE)


def _degistir(metin: str, eski: str, yeni: str) -> str:
    return _uygula(metin, [("sabit", eski, yeni)])


# =================================================================================================
# ŞİMLER
# =================================================================================================
SIM_SUDO = '#!/bin/sh\nexec "$@"\n'

SIM_CHOWN = r'''#!/bin/sh
printf 'chown %s\n' "$*" >> "$SAHTE_KOK/.sahte/olay.log"
'''

SIM_INSTALL = r'''#!__PY__
"""install: `-o KULLANICI -g GRUP` düşer (test kullanıcısı root değildir), gerisi gerçek install'a."""
import os, sys
a, out, i = sys.argv[1:], [], 0
while i < len(a):
    if a[i] in ("-o", "-g"):
        i += 2
        continue
    out.append(a[i])
    i += 1
os.execv("/usr/bin/install", ["install"] + out)
'''

SIM_STAT = r'''#!__PY__
"""GNU `stat -c FMT DOSYA` (%a %U %G) — macOS stat `-c` bilmez. Öteki biçimler gerçek stat'a."""
import grp, os, pwd, stat, sys
a = sys.argv[1:]
if len(a) == 3 and a[0] == "-c":
    if not os.path.exists(a[2]):
        sys.stderr.write("stat: cannot statx '%s': No such file or directory\n" % a[2])
        sys.exit(1)
    st = os.stat(a[2])
    sys.stdout.write(a[1].replace("%a", format(stat.S_IMODE(st.st_mode), "o"))
                         .replace("%U", pwd.getpwuid(st.st_uid).pw_name)
                         .replace("%G", grp.getgrgid(st.st_gid).gr_name) + "\n")
    sys.exit(0)
os.execv("/usr/bin/stat", ["stat"] + a)
'''

SIM_SED = r'''#!__PY__
"""GNU sed'in `_token_oku` ifadesi. Okunamayan dosya: GNU gibi hata metni + ÇIKIŞ 2."""
import os, sys
a = sys.argv[1:]
if len(a) == 3 and a[:2] == ["-n", "__IFADE__"]:
    if not os.path.isfile(a[2]):
        sys.stderr.write("sed: can't read %s: No such file or directory\n" % a[2])
        sys.exit(2)
    with open(a[2], encoding="utf-8") as fh:
        for s in fh.read().splitlines(keepends=True):
            sys.stdout.write(s[len("__ONEK__"):] if s.startswith("__ONEK__") else s)
    sys.exit(0)
os.execv("/usr/bin/sed", ["sed"] + a)
'''

SIM_SYSTEMCTL = r'''#!__PY__
"""systemctl MODELİ (v559). Etkin jeton YALNIZ dosyaya yazılır (.sahte/etkin), hiçbir çıktıya basılmaz."""
import os, sys
K = os.environ["SAHTE_KOK"]
S = os.path.join(K, ".sahte")
BIRIM = K + "__BIRIM__"
KRED = K + "__KRED__"
ENVF = K + "__ENVF__"
ONEK = "__ONEK__"
a = sys.argv[1:]
with open(os.path.join(S, "olay.log"), "a", encoding="utf-8") as fh:
    fh.write("systemctl " + " ".join(a).replace(K, "<K>") + "\n")


def oku(p):
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def etkin():
    """None = birim BAŞLAMAZ (LoadCredential kaynağı yok ya da SAHTE_ACILMAZ)."""
    cred = ""
    if os.path.exists(os.path.join(BIRIM, "50-dash-credential.conf")):
        if os.environ.get("SAHTE_ACILMAZ") == "1":
            return None
        ham = oku(KRED)
        if ham is None:
            return None
        satirlar = ham.strip().splitlines()
        cred = satirlar[0].strip() if satirlar else ""
        if cred.startswith(ONEK):
            cred = cred[len(ONEK):].strip()
    env = ""
    if not os.path.exists(os.path.join(BIRIM, "51-dash-env-kaldir.conf")):
        for s in (oku(ENVF) or "").splitlines():
            if s.startswith(ONEK):
                env = s[len(ONEK):]
    mod = os.environ.get("SAHTE_UYGULAMA", "yeni")
    if mod == "eski":
        return env
    if mod == "sabit":
        return "__SABIT__"
    return cred or env


def yaz(ad, deger):
    with open(os.path.join(S, ad), "w", encoding="utf-8") as fh:
        fh.write(deger)


def aktif():
    return oku(os.path.join(S, "durum")) == "aktif"


if a[:1] == ["--version"]:
    sys.stdout.write("systemd 255 (255.4-1ubuntu8.10)\n+PAM +AUDIT +SELINUX\n")
elif a[:1] == ["restart"]:
    e = etkin()
    yaz("durum", "aktif" if e is not None else "dusuk")
    yaz("etkin", e or "")
elif a[:1] == ["is-active"]:
    if "--quiet" not in a:
        sys.stdout.write(("active" if aktif() else "failed") + "\n")
    sys.exit(0 if aktif() else 3)
elif a[:1] == ["show"]:
    kurulu = os.path.exists(os.path.join(BIRIM, "50-dash-credential.conf"))
    sys.stdout.write(("dash_token:" + KRED if kurulu else "") + "\n")
'''


def _yollar(kok: pathlib.Path) -> dict[str, pathlib.Path]:
    metin = BETIK.read_text(encoding="utf-8")
    return {ad: kok / _sabit(metin, ad).lstrip("/") for ad in ("KRED", "ENVF", "BIRIM")}


def _bin(kok: pathlib.Path) -> None:
    metin = BETIK.read_text(encoding="utf-8")
    yer = {"__PY__": sys.executable, "__IFADE__": SED_IFADESI, "__ONEK__": DAGINIK_ONEK,
           "__SABIT__": SABIT_JETON, "__BIRIM__": _sabit(metin, "BIRIM"),
           "__KRED__": _sabit(metin, "KRED"), "__ENVF__": _sabit(metin, "ENVF")}
    b = kok / ".bin"
    b.mkdir()
    for ad, sim in (("sudo", SIM_SUDO), ("chown", SIM_CHOWN), ("install", SIM_INSTALL),
                    ("stat", SIM_STAT), ("sed", SIM_SED), ("systemctl", SIM_SYSTEMCTL)):
        for k, v in yer.items():
            sim = sim.replace(k, v)
        (b / ad).write_text(sim, encoding="utf-8")
        (b / ad).chmod(0o755)


def _yonlendir(metin: str, kok: pathlib.Path, port: int) -> str:
    kred, envf, birim, api = (_sabit(metin, a) for a in ("KRED", "ENVF", "BIRIM", "API"))
    kred_dizin = os.path.dirname(kred)
    metin = _uygula(metin, [
        ("sabit", f"BIRIM={birim}\n", f"BIRIM={kok}{birim}\n"),
        ("sabit", f"KRED={kred}\n", f"KRED={kok}{kred}\n"),
        ("sabit", f"ENVF={envf}\n", f"ENVF={kok}{envf}\n"),
        ("sabit", f"API={api}\n", f"API=http://127.0.0.1:{port}\n"),
        ("sabit", f"-o root -g root {kred_dizin}\n", f"-o root -g root {kok}{kred_dizin}\n"),
    ])
    kalan = [y for s in _kod(metin).splitlines() for y in re.findall(r"(?<![\w/.-])/(?:etc|opt)/[\w./-]*", s)]
    assert not kalan, f"yönlendirilmemiş mutlak yol: {kalan}"
    return metin


def _ortam(kok: pathlib.Path, **ek: str) -> dict:
    atla = ("MERIDIAN_DASH_TOKEN", "TOKEN", "CREDENTIALS_DIRECTORY", "SAHTE_UYGULAMA", "SAHTE_ACILMAZ")
    ortam = {k: v for k, v in os.environ.items() if k not in atla}
    ortam.update(PATH=f"{kok / '.bin'}:{os.environ['PATH']}", SAHTE_KOK=str(kok))
    ortam.update(ek)
    return ortam


def _dunya(tmp_path: pathlib.Path, metin: str, hal: str, port: int, ad: str = "d", **ek: str) -> pathlib.Path:
    """Üç dünya: `tarihsel` (geçiş öncesi: yalnız `.dash.env`) · `faz1_sonrasi` (iki kanal aynı jetonda,
    50 kurulu) · `bugun` (A1 2026-09-26: `.dash.env` YOK, meridian.service.d'nin BÜTÜN drop-in'leri kurulu
    — A0 rolü `dropinler.yml` glob'la hepsini kopyalar — ve KRED Vault Agent'ın render ettiği değer).
    Root modellenmez: betiğin YAZACAĞI dosyalar tohumda sahibine yazılabilir (0600)."""
    kok = tmp_path / ad
    y = _yollar(kok)
    for p in (y["KRED"].parent, y["ENVF"].parent, y["BIRIM"].parent, kok / ".sahte"):
        p.mkdir(parents=True, exist_ok=True)
    if hal == "tarihsel":
        y["ENVF"].write_text(f"{DAGINIK_ONEK}{ESKI_ORTAM}\n", encoding="utf-8")
        y["ENVF"].chmod(0o600)
    elif hal == "faz1_sonrasi":
        y["ENVF"].write_text(f"{DAGINIK_ONEK}{ARA_JETON}\n", encoding="utf-8")
        y["ENVF"].chmod(0o600)
        y["KRED"].write_text(ARA_JETON + "\n", encoding="utf-8")
        y["KRED"].chmod(0o400)
        y["BIRIM"].mkdir()
        shutil.copy(DROPIN_DIZIN / "50-dash-credential.conf", y["BIRIM"])
    elif hal == "bugun":
        y["KRED"].write_text(KASA_JETON, encoding="utf-8")     # Agent şablonu sondaki satırsonu yazmaz
        y["KRED"].chmod(0o600)
        y["BIRIM"].mkdir()
        for p in sorted(DROPIN_DIZIN.glob("*.conf")):
            shutil.copy(p, y["BIRIM"])
    else:
        raise AssertionError(f"bilinmeyen dünya: {hal}")
    shutil.copytree(DROPIN_DIZIN, kok / "betik" / DROPIN_DIZIN.name)
    hedef = kok / "betik" / BETIK.name
    hedef.write_text(_yonlendir(metin, kok, port), encoding="utf-8")
    hedef.chmod(0o755)
    _bin(kok)
    r = subprocess.run([str(kok / ".bin" / "systemctl"), "restart", "meridian"], capture_output=True,
                       text=True, env=_ortam(kok, **ek), timeout=60)
    assert r.returncode == 0, "dünya tohumu: systemctl modeli başlamadı"
    (kok / ".sahte" / "olay.log").unlink()
    return kok


def _kos(pano: dict, kok: pathlib.Path, *arg: str, **ek: str) -> subprocess.CompletedProcess:
    pano["kok"] = kok
    pano["goruntuler"].clear()
    pano["istekler"].clear()
    return subprocess.run(["bash", str(kok / "betik" / BETIK.name), *arg], capture_output=True, text=True,
                          encoding="utf-8", env=_ortam(kok, **ek), timeout=120)


def _etiket(deger: str | None) -> str:
    if deger is None:
        return "YOK"
    if deger == "":
        return "BOS"
    if deger in TOHUMLAR:
        return TOHUMLAR[deger]
    if re.fullmatch(r"[0-9a-f]{48}", deger):
        return "URETILEN_48HEX"
    return "BASKA"


def _kred(kok: pathlib.Path) -> str | None:
    p = _yollar(kok)["KRED"]
    return p.read_text(encoding="utf-8").strip() if p.exists() else None


def _imza(kok: pathlib.Path) -> dict:
    """Dünyanın DEĞERSİZ imzası: etiketler, eşitlikler, modlar, dosya adları."""
    y = _yollar(kok)

    def _mod(p: pathlib.Path):
        return format(stat.S_IMODE(p.stat().st_mode), "o") if p.exists() else None

    kred = _kred(kok)
    envf = None
    if y["ENVF"].exists():
        envf = ""
        for s in y["ENVF"].read_text(encoding="utf-8").splitlines():
            if s.startswith(DAGINIK_ONEK):
                envf = s[len(DAGINIK_ONEK):]
    etkin = (kok / ".sahte" / "etkin").read_text(encoding="utf-8")
    return {
        "kred": _etiket(kred), "kred_mod": _mod(y["KRED"]),
        "envf": _etiket(envf), "envf_mod": _mod(y["ENVF"]),
        "envf_kred_esit": envf is not None and envf == kred,
        "etkin": _etiket(etkin), "etkin_kred_esit": etkin == kred,
        "yedekler": sorted(re.sub(r"\d{12}$", "<T>", p.name)
                           for p in y["ENVF"].parent.glob(y["ENVF"].name + ".*")),
        "dropin": sorted(p.name for p in y["BIRIM"].iterdir()) if y["BIRIM"].exists() else None,
        "durum": (kok / ".sahte" / "durum").read_text(encoding="utf-8"),
    }


def _olaylar(kok: pathlib.Path) -> list[str]:
    p = kok / ".sahte" / "olay.log"
    return p.read_text(encoding="utf-8").replace(str(kok), "<K>").splitlines() if p.exists() else []


@pytest.fixture
def pano():
    """Sahte pano. `/api/*` isteği ANINDA torun süreçlerin argv görüntüsü alınır; yetki yalnız ETKİN
    jetonla EŞİTLİKTİR (değer hiçbir yere yazılmaz, yalnız bool)."""
    durum: dict = {"kok": None, "goruntuler": [], "istekler": []}

    class _Isleyici(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 — BaseHTTPRequestHandler sözleşmesi
            if self.path.startswith("/api/"):
                durum["goruntuler"].append(_torun_argvleri_goruntusu())
                etkin = (durum["kok"] / ".sahte" / "etkin").read_text(encoding="utf-8")
                baslik = self.headers.get("x-meridian-token")
                yetkili = bool(etkin) and baslik == etkin
                durum["istekler"].append((self.path, yetkili, baslik is not None))
                kod = 200 if yetkili else 401
            elif self.path == "/healthz":
                kod = 200
            else:
                kod = 404
            govde = b"{}"
            self.send_response(kod)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(govde)))
            self.end_headers()
            self.wfile.write(govde)

        def log_message(self, *a):  # sessiz-yutma: sahte sunucunun erişim günlüğü test çıktısını kirletmesin
            return

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Isleyici)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    durum["port"] = srv.server_address[1]
    yield durum
    srv.shutdown()
    srv.server_close()


# ---- ölçüm yardımcıları (hepsi bool/sayı/ad döndürür — değer DEĞİL) -----------------------------
def _jetonlar(kok: pathlib.Path) -> list[str]:
    return [j for j in [_kred(kok), *TOHUMLAR] if j]


def _argv_olcumu(pano: dict, jetonlar: list[str]) -> tuple[bool, int, bool]:
    """(pozitif kontrol: ps curl'ü /api/hermes ile gördü mü · jeton taşıyan argv sayısı · ps hep rc 0)."""
    hedef = f"127.0.0.1:{pano['port']}/api/hermes"
    gordu = any(hedef in a for _, g in pano["goruntuler"] for a in g)
    sizan = sum(1 for _, g in pano["goruntuler"] for a in g if any(j in a for j in jetonlar))
    return gordu, sizan, all(k == 0 for k, _ in pano["goruntuler"])


def _ciktida_jeton(r: subprocess.CompletedProcess, jetonlar: list[str]) -> int:
    return sum(1 for j in jetonlar if j in r.stdout or j in r.stderr)


def _yer_beyani_eksikleri(r: subprocess.CompletedProcess, kok: pathlib.Path) -> list[str]:
    """Faz-1 çıktısı iki kopyanın YOLUNU + ÖLÇÜLEN izin/sahibini (dosyanın kendisinden) ve okuma
    KOMUTUNU taşıyor mu. Dönen: eksik öğelerin ADLARI."""
    y = _yollar(kok)
    eksik = []
    for ad in ("KRED", "ENVF"):
        st = y[ad].stat()
        beklenen = (f"{y[ad]} ({format(stat.S_IMODE(st.st_mode), 'o')} "
                    f"{pwd.getpwuid(st.st_uid).pw_name}:{grp.getgrgid(st.st_gid).gr_name})")
        if beklenen not in r.stdout:
            eksik.append(f"{ad}: yol + ölçülen izin/sahip")
    if f"sudo cat {y['KRED']}" not in r.stdout:
        eksik.append("okuma komutu")
    return eksik


# =================================================================================================
# KABUK SÖZCÜKLEYİCİSİ — statik baskı çivisinin aleti (A2/A3)
# =================================================================================================
def _sozcukle(metin: str) -> list[list[tuple[str, str]]]:
    """Kabuk metnini BORU HATLARINA böler: [[(ham, genisleyen), ...], ...]. Tırnak ve `$( )` farkındadır:
    tırnak/komut ikamesi İÇİNDEKİ `|` `;` `&&` `||` ve satır sonu ayırıcı DEĞİLDİR; yorumlar atılır.
    `genisleyen` segmentin kabuğun GENİŞLETECEĞİ kısmıdır: tek tırnak içeriği ve `\\$` kaçışı çıkar.
    Kapsam bilinçli dar — bu betiğin sözdizimi; heredoc YOK (A0 ön-koşul olarak ölçer)."""
    hatlar: list[list[tuple[str, str]]] = []
    hat: list[tuple[str, str]] = []
    ham: list[str] = []
    gen: list[str] = []
    yigin: list[str] = []

    def ekle(s: str, genislesin: bool = True) -> None:
        ham.append(s)
        if genislesin:
            gen.append(s)

    def seg_bitir() -> None:
        s = "".join(ham).strip()
        if s:
            hat.append((s, "".join(gen).strip()))
        ham.clear()
        gen.clear()

    def hat_bitir() -> None:
        seg_bitir()
        if hat:
            hatlar.append(list(hat))
            hat.clear()

    i, n = 0, len(metin)
    while i < n:
        c = metin[i]
        ust = yigin[-1] if yigin else ""
        if c == "\\" and i + 1 < n:
            if metin[i + 1] == "\n" and not yigin:
                i += 2                                  # satır devamı
                continue
            ekle(metin[i:i + 2], genislesin=metin[i + 1] != "$")
            i += 2
            continue
        if c == "'" and ust != '"':
            j = metin.find("'", i + 1)
            j = n - 1 if j < 0 else j
            ekle(metin[i:j + 1], genislesin=False)
            i = j + 1
            continue
        if c == "$" and metin[i + 1:i + 2] == "(":
            yigin.append("(")
            ekle("$(")
            i += 2
            continue
        if c == ")" and ust == "(":
            yigin.pop()
            ekle(c)
            i += 1
            continue
        if c == '"':
            if ust == '"':
                yigin.pop()
            else:
                yigin.append('"')
            ekle(c)
            i += 1
            continue
        if yigin:
            ekle(c)
            i += 1
            continue
        onceki = metin[i - 1] if i else "\n"
        if c == "#" and onceki in " \t\n;&|(":
            j = metin.find("\n", i)
            i = n if j < 0 else j
            continue
        if c in "\n;":
            hat_bitir()
            i += 1
            continue
        if c in "|&" and metin[i + 1:i + 2] == c:
            hat_bitir()
            i += 2
            continue
        if c == "|":
            seg_bitir()
            i += 1
            continue
        if c == "&" and onceki not in "<>":
            hat_bitir()
            i += 1
            continue
        ekle(c)
        i += 1
    hat_bitir()
    return hatlar


_ONEK = re.compile(r"^(?:\w+\(\)\s*\{|\{|then|do|else|elif|if|while|until|!|sudo|[A-Za-z_]\w*=\S*)\s+")


def _komut_adi(segment: str) -> str:
    s = segment
    while (m := _ONEK.match(s)) is not None:
        s = s[m.end():]
    return s.split()[0] if s.split() else ""


def _yazicilar(metin: str) -> set[str]:
    """Çıktıya basan komutlar: `echo` `printf` + betikte `echo "... $*"` gövdeli her yardımcı (die/oldu)."""
    return {"echo", "printf"} | set(re.findall(r"^(\w+)\(\)\s*\{\s*echo\b[^\n]*\$\*", metin, re.M))


def _jeton_degiskenleri(metin: str) -> set[str]:
    """Jeton taşıyan değişkenler BETİKTEN türer: `openssl rand` üretimi · `_token_oku` · `sudo cat "$KRED"`."""
    return set(re.findall(r"\b(\w+)=\"\$\((?:openssl rand\b|_token_oku\b|sudo cat \"\$KRED\")", metin))


def _baski_ihlalleri(metin: str) -> tuple[list[str], int]:
    """(ihlaller, korunan). İhlal: jeton değişkeni genişleten bir yazıcı ya boru hattının SON halkasıdır
    (çıktı terminale/stderr'e gider) ya da çıktısını `>/dev/null`suz bir `tee`ye verir (tee stdout'a da
    yazar). `korunan`: jetonu bir borudan TÜKETİCİYE veren yazıcı sayısı (pozitif kontrol)."""
    degiskenler = _jeton_degiskenleri(metin)
    if not degiskenler:
        return ["jeton değişkeni türetilemedi (ölçüm kör)"], 0
    yazicilar = _yazicilar(metin)
    ad = "|".join(sorted(degiskenler))
    genis = re.compile(r"\$(?:\{(?:%s)\}|(?:%s)\b)" % (ad, ad))
    ihlal: list[str] = []
    korunan = 0
    for hat in _sozcukle(metin):
        for k, (ham, gen) in enumerate(hat):
            if _komut_adi(ham) not in yazicilar or not genis.search(gen):
                continue
            if k == len(hat) - 1:
                ihlal.append(f"çıktıya: {ham[:90]}")
                continue
            sonraki = hat[k + 1][0]
            if _komut_adi(sonraki) == "tee" and not re.search(r">\s*/dev/null", sonraki):
                ihlal.append(f"tee stdout'a da yazar: {ham[:60]} | {sonraki[:40]}")
                continue
            korunan += 1
    return ihlal, korunan


def _baslik_argv_ihlalleri(metin: str) -> list[str]:
    """Kod satırlarında `-H "<...>$` (başlık argümanında genişleme) + stdin başlığının varlığı."""
    kod = _kod(metin)
    ihlal = []
    if re.search(r"""-H\s+["'][^"'@]*\$""", kod):
        ihlal.append("başlık argümanında değişken genişlemesi (argv)")
    if "-H @-" not in kod:
        ihlal.append("başlık STDIN'den verilmiyor")
    if "printf 'x-meridian-token: %s\\n'" not in kod:
        ihlal.append("başlık printf (yerleşik) ile üretilmiyor")
    return ihlal


# =================================================================================================
# A) STATİK
# =================================================================================================
def test_A0_SIM_ONKOSULLARI_sabitler_TEK_sed_ifadesi_TEK_heredoc_YOK_sozdizimi_TEMIZ():
    metin = BETIK.read_text(encoding="utf-8")
    for ad in ("BIRIM", "KRED", "ENVF", "API"):
        _sabit(metin, ad)
    assert metin.count(f"sed -n '{SED_IFADESI}'") == 1, "sed şimi betiğin ifadesini modellemiyor"
    assert "<<" not in _kod(metin), "sözcükleyici heredoc bilmez — kapsam dışı sözdizimi"
    assert sorted(p.name for p in DROPIN_DIZIN.glob("*.conf")), "drop-in kaynağı yok"
    r = subprocess.run(["bash", "-n", str(BETIK)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr[-300:]


def test_A1_STATIK_baslik_STDINden_printf_YERLESIK_argvde_GENISLEME_YOK():
    assert _baslik_argv_ihlalleri(BETIK.read_text(encoding="utf-8")) == []
    r = subprocess.run(["bash", "-c", "type -t printf"], capture_output=True, text=True, timeout=30)
    assert r.stdout.strip() == "builtin", "printf yerleşik değil: süreç doğurur, argv'ye girer"


def test_A2_STATIK_jeton_degiskeni_HICBIR_baskiya_gitmez_ve_olcum_KOR_DEGIL():
    metin = BETIK.read_text(encoding="utf-8")
    assert {"yeni", "eski", "tok"} <= _jeton_degiskenleri(metin), "jeton değişkenleri türetilemedi"
    assert {"echo", "printf", "die", "oldu"} <= _yazicilar(metin), "yazıcı yardımcıları türetilemedi"
    ihlal, korunan = _baski_ihlalleri(metin)
    assert ihlal == [], ihlal
    # POZİTİF KONTROL: `printf … "$yeni"` üç kez bir TÜKETİCİYE borulanır (biçim grep'i · iki tee).
    assert korunan >= 3, f"sözcükleyici korunan yazıcıları görmüyor ({korunan}) — ölçüm kör"


SOZCUK_ONEK = ('yeni="$(openssl rand -hex 24)"\neski="$(_token_oku "$F")"\n'
               "tok=\"$(sudo cat \"$KRED\" | tr -d '\\r\\n')\"\n"
               'die() { echo "!! $*" >&2; exit 1; }\noldu() { echo "  ok $*"; }\n')
SOZCUK_ORNEKLERI = {
    'echo "yeni: $yeni"': 1,
    'printf "%s\\n" "${yeni}"': 1,
    'oldu "t=$tok"': 1,
    'die "iki\n   satır $eski"': 1,
    'echo "a # $yeni"': 1,
    'echo "a | b; $yeni"': 1,
    '[ -n "$eski" ] || echo "uyarı $eski"': 1,
    "printf '%s\\n' \"$yeni\" | sudo tee \"$K\"": 1,
    "echo 'düz metin $yeni'": 0,
    '# echo "$yeni"': 0,
    "x=\"$(printf '%s' \"$yeni\" | tr a b)\"": 0,
    "printf '%s\\n' \"$yeni\" | sudo tee \"$K\" >/dev/null": 0,
    'echo "kaçış \\$yeni"': 0,
    'echo "$yeniden"': 0,
    "echo \"x | $(echo y) ; z\"": 0,
}


@pytest.mark.parametrize("ornek", list(SOZCUK_ORNEKLERI))
def test_A3_SOZCUKLEYICI_pozitif_ve_negatif_kontrol(ornek):
    ihlal, _ = _baski_ihlalleri(SOZCUK_ONEK + ornek + "\n")
    assert len(ihlal) == SOZCUK_ORNEKLERI[ornek], ihlal


def test_A4_SINIF_TARAMASI_v556_yeni_bicimde_SESSIZ_eski_bicimde_OTER(tmp_path):
    ihlal, sayac = _sinif_tara([BETIK])
    assert ihlal == [], ihlal
    assert sayac["arguman"] >= 1, "tarayıcı betikte hiç başlık argümanı görmedi (kör)"
    eski = tmp_path / "eski" / BETIK.name
    eski.parent.mkdir()
    eski.write_text(_eski_bicim(), encoding="utf-8")
    ihlal, _ = _sinif_tara([eski], kok=tmp_path)
    assert [(i[0], i[2]) for i in ihlal] == [(f"eski/{BETIK.name}", "x-meridian-token")]


# =================================================================================================
# İDDİA GÜVENLİĞİ — pytest'in iddia açıklaması, iddia İFADESİNDEKİ çağrı ve öznitelikleri açar
# (`where 1 = _ciktida_jeton(CompletedProcess(... stdout='…'), ['…'])`). İlk kırmızı koşumda sahte
# değerler günlüğe böyle düştü (2026-09-26, maskelendi). Kural: iddia ifadesinde YALNIZ yerel ad —
# çıkış kodu, maskeli metin, sayı, etiket; `CompletedProcess` ya da jeton listesi iddia ifadesine GİRMEZ.
# =================================================================================================
_DEGER = re.compile(r"SAHTE-[A-Z0-9-]+|\b[0-9a-f]{48}\b")


def _maske(s: str) -> str:
    return _DEGER.sub("<DEGER>", s)


def _sonuc(r: subprocess.CompletedProcess) -> tuple[int, str, str]:
    """(çıkış kodu, maskeli stdout, maskeli stderr)."""
    return r.returncode, _maske(r.stdout), _maske(r.stderr)


# =================================================================================================
# B) DİNAMİK
# =================================================================================================
def test_B1_DINAMIK_faz1_jeton_HICBIR_torunun_argvsinde_YOK_ve_baslik_ULASIR(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "tarihsel", pano["port"])
    kod, _, hata = _sonuc(_kos(pano, kok, "--faz1"))
    assert kod == 0, hata[-300:]
    uretilen = _imza(kok)["kred"]
    assert uretilen == "URETILEN_48HEX"
    gordu, sizan, rc_ok = _argv_olcumu(pano, _jetonlar(kok))
    assert rc_ok and gordu, "POZİTİF KONTROL düştü: ps curl'ün argv'sini görmedi"
    assert sizan == 0, f"jeton {sizan} sürecin argv'sinde"
    istekler = list(pano["istekler"])
    assert istekler == [("/api/hermes", True, True)], "başlık sunucuya ULAŞMADI ya da yanlış değerle"


def test_B2_DINAMIK_faz2_iki_olcumde_de_jeton_argvde_YOK_ve_baslik_ULASIR(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "faz1_sonrasi", pano["port"])
    kod, _, hata = _sonuc(_kos(pano, kok, "--faz2"))
    assert kod == 0, hata[-300:]
    gordu, sizan, rc_ok = _argv_olcumu(pano, _jetonlar(kok))
    assert rc_ok and gordu, "POZİTİF KONTROL düştü: ps curl'ün argv'sini görmedi"
    assert sizan == 0, f"jeton {sizan} sürecin argv'sinde"
    istekler = list(pano["istekler"])
    assert istekler == [("/api/hermes", True, True)] * 2


def test_B3_CIKTI_faz1_YENI_ve_ESKI_jeton_HICBIR_kanalda_YOK(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "tarihsel", pano["port"])
    r = _kos(pano, kok, "--faz1")
    kod, _, hata = _sonuc(r)
    assert kod == 0, hata[-300:]
    uretilen = _imza(kok)["kred"]
    assert uretilen == "URETILEN_48HEX", "ölçülecek yeni jeton yok"
    sizan = _ciktida_jeton(r, _jetonlar(kok))
    assert sizan == 0, f"{sizan} jeton stdout/stderr'de"


def test_B3b_CIKTI_faz2_jeton_HICBIR_kanalda_YOK(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "faz1_sonrasi", pano["port"])
    r = _kos(pano, kok, "--faz2")
    kod, _, hata = _sonuc(r)
    assert kod == 0, hata[-300:]
    sizan = _ciktida_jeton(r, _jetonlar(kok))
    assert sizan == 0, f"{sizan} jeton stdout/stderr'de"


def test_B4_YER_BEYANI_iki_kopya_yol_OLCULEN_izin_sahip_ve_OKUMA_KOMUTU(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "tarihsel", pano["port"])
    r = _kos(pano, kok, "--faz1")
    kod, _, hata = _sonuc(r)
    assert kod == 0, hata[-300:]
    eksik = _yer_beyani_eksikleri(r, kok)
    assert eksik == []
    i = _imza(kok)
    modlar = (i["kred_mod"], i["envf_mod"])
    assert modlar == ("400", "600"), "beyan edilen izinler betiğin yazdığı DEĞİL"


# =================================================================================================
# C) DAVRANIŞ — ESKİ BİÇİMLE BİREBİR
# =================================================================================================
C_SENARYOLARI = [
    ("tarihsel", "", {}),
    ("tarihsel", "--faz1", {}),
    ("tarihsel", "--faz1", {"SAHTE_UYGULAMA": "sabit"}),
    ("tarihsel", "--faz1", {"SAHTE_ACILMAZ": "1"}),
    ("faz1_sonrasi", "--faz2", {}),
    ("faz1_sonrasi", "--faz2", {"SAHTE_UYGULAMA": "eski"}),
    ("faz1_sonrasi", "--geri-al", {}),
    ("bugun", "", {}),
    ("bugun", "--faz1", {}),
    ("bugun", "--faz2", {}),
    ("bugun", "--geri-al", {}),
    ("bugun", "--bilinmeyen", {}),
]
_FAZ1_SONU = re.compile(r"(?ms)^>> FAZ 1 TAMAM\..*?(?=^>> Faz 2'ye GEÇMEDEN)")


def _senaryo(tmp_path, pano, metin, hal, arg, ek, ad) -> dict:
    """Bir senaryonun DEĞERSİZ özeti. Faz-1 kuyruğu (jeton satırı ↔ yer beyanı) iki biçimde de tek bir
    işaretçiye indirgenir — o blok bilerek değişti ve B3/B4 ölçer; geri kalan her şey birebir kıyaslanır."""
    kok = _dunya(tmp_path, metin, hal, pano["port"], ad=ad, **ek)
    r = _kos(pano, kok, *([arg] if arg else []), **ek)
    norm = (lambda s: _maske(_FAZ1_SONU.sub("<FAZ1-SONU>\n", s.replace(str(kok), "<K>"))))
    return {"kod": r.returncode, "stdout": norm(r.stdout), "stderr": norm(r.stderr),
            "olaylar": _olaylar(kok), "imza": _imza(kok), "istekler": list(pano["istekler"])}


def _farklar(tmp_path, pano, eski_metin, yeni_metin, hal, arg, ek) -> tuple[list[str], dict]:
    e = _senaryo(tmp_path, pano, eski_metin, hal, arg, ek, "eski")
    y = _senaryo(tmp_path, pano, yeni_metin, hal, arg, ek, "yeni")
    return [k for k in e if e[k] != y[k]], y


@pytest.mark.parametrize("hal,arg,ek", C_SENARYOLARI,
                         ids=[f"{h}{a or '_durum'}{'_' + '_'.join(e.values()) if e else ''}"
                              for h, a, e in C_SENARYOLARI])
def test_C_DAVRANIS_ESKI_bicimle_BIREBIR(tmp_path, pano, hal, arg, ek):
    yeni = BETIK.read_text(encoding="utf-8")
    farklar, y = _farklar(tmp_path, pano, _eski_bicim(yeni), yeni, hal, arg, ek)
    assert farklar == [], f"eski↔yeni ayrışan alanlar: {farklar}"
    if (hal, arg, ek) == ("tarihsel", "--faz1", {}):
        basari = y["kod"] == 0 and "<FAZ1-SONU>" in y["stdout"]
        assert basari, "faz-1 başarı yolu koşmadı (C kör)"


# =================================================================================================
# D) BUGÜNKÜ DÜNYA — EMEKLİLİK KANITI (davranışı sabitler; karar Rol-1'in)
# =================================================================================================
def test_D1_KRED_Vault_Agent_RENDER_HEDEFI_rotasyonun_KASA_YOLU_sir_rotasyonda_betik_kasayi_BILMEZ():
    metin = BETIK.read_text(encoding="utf-8")
    kred = _sabit(metin, "KRED")
    envanter = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))
    girdi = [g for g in envanter["vault_kv"] if g.get("hedef") == kred]
    assert len(girdi) == 1 and girdi[0].get("rotasyon_siri") == "MERIDIAN_DASH_TOKEN"
    hedef_mi = f'destination = "{kred}"' in AGENT_HCL.read_text(encoding="utf-8")
    assert hedef_mi, "KRED Agent render hedefi değil"
    rot = SIR_ROTASYON.read_text(encoding="utf-8")
    assert re.search(r"^dash\(\) \{", rot, re.M), "sir_rotasyon.sh --dash alt komutu yok"
    tabloda = f"dash MERIDIAN_DASH_TOKEN dosya {kred} " in rot
    assert tabloda, "rotasyon tablosu KRED'i yazmıyor"
    assert re.search(r"^\s*kapi\|dash\|apisix-admin\) echo b64 ;;", rot, re.M), "--dash --uret sınıfı yok"
    kasayi_bilir = "vault" in _kod(metin).lower()
    assert not kasayi_bilir, "betik kasayı biliyor — D ölçümü yeniden yapılmalı"


def test_D2_BUGUNKU_DUNYA_faz1_ENVF_yok_diye_SESSIZ_cikis_2_HICBIR_sey_yazilmaz(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "bugun", pano["port"])
    once = _imza(kok)
    kod, cikti, hata = _sonuc(_kos(pano, kok, "--faz1"))
    assert kod == 2
    assert cikti.strip() == "=== FAZ 1: rotasyon + LoadCredential kanalı ===" and hata == ""
    sonra = _imza(kok)
    assert sonra == once
    olaylar, istekler = _olaylar(kok), list(pano["istekler"])
    assert olaylar == ["systemctl --version"] and istekler == []


def test_D3_BUGUNKU_DUNYA_faz2_ENVF_yok_diye_cp_de_DUSER_die_DEGIL_durum_DEGISMEZ(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "bugun", pano["port"])
    once = _imza(kok)
    kod, cikti, hata = _sonuc(_kos(pano, kok, "--faz2"))
    assert kod == 1
    assert "farksal ölçüm: ortam kanalına sahte değer konuyor" in cikti
    cp_hatasi = "!!" not in hata and _yollar(kok)["ENVF"].name in hata
    assert cp_hatasi, "düşüş cp'nin kendi hatası değil"
    sonra = _imza(kok)
    assert sonra == once
    olaylar, istekler = _olaylar(kok), list(pano["istekler"])
    assert olaylar == [] and istekler == []


def test_D4_BUGUNKU_DUNYA_geri_al_TEK_kanali_KALDIRIR_etkin_jeton_BOS_ama_ENVF_yururlukte_DER(tmp_path, pano):
    kok = _dunya(tmp_path, BETIK.read_text(encoding="utf-8"), "bugun", pano["port"])
    once = _imza(kok)
    kod, cikti, hata = _sonuc(_kos(pano, kok, "--geri-al"))
    assert kod == 0, hata[-300:]
    sonra = _imza(kok)
    assert (once["etkin"], sonra["etkin"]) == ("KASA_JETON", "BOS")
    assert set(sonra["dropin"]) == set(once["dropin"]) - {"50-dash-credential.conf", "51-dash-env-kaldir.conf"}
    envf = _yollar(kok)["ENVF"]
    yanlis_guvence = f"({envf} yürürlükte)" in cikti and not envf.exists()
    assert yanlis_guvence, "yanlış güvence ölçülemedi"


# =================================================================================================
# M) MUTASYONLAR — mutant tmp'de koşar, özgün betik değişmez
# =================================================================================================
def test_M1_MUT_baslik_ARGVye_donerse_B1_A1_A4_KIRMIZI(tmp_path, pano):
    mutant = _uygula(BETIK.read_text(encoding="utf-8"), [ESKI_AUTH])
    kok = _dunya(tmp_path, mutant, "tarihsel", pano["port"])
    kod, _, hata = _sonuc(_kos(pano, kok, "--faz1"))
    assert kod == 0, hata[-300:]
    gordu, sizan, _ = _argv_olcumu(pano, _jetonlar(kok))
    assert gordu and sizan >= 1, "mutasyon ISIRMADI: eski biçimde de jeton argv'de görünmedi (B1 kör)"
    a1 = _baslik_argv_ihlalleri(mutant)
    assert a1, "A1 kör"
    m = tmp_path / "m" / BETIK.name
    m.parent.mkdir()
    m.write_text(mutant, encoding="utf-8")
    a4, _ = _sinif_tara([m], kok=tmp_path)
    assert a4, "A4 kör"


def test_M2_MUT_yeni_jeton_BASILIRSA_B3_B4_A2_KIRMIZI(tmp_path, pano):
    mutant = _uygula(BETIK.read_text(encoding="utf-8"), [ESKI_KUYRUK])
    kok = _dunya(tmp_path, mutant, "tarihsel", pano["port"])
    r = _kos(pano, kok, "--faz1")
    kod, _, hata = _sonuc(r)
    assert kod == 0, hata[-300:]
    sizan = _ciktida_jeton(r, _jetonlar(kok))
    assert sizan >= 1, "B3 kör"
    eksik = _yer_beyani_eksikleri(r, kok)
    assert eksik, "B4 kör"
    a2, _ = _baski_ihlalleri(mutant)
    assert a2, "A2 kör"


def test_M3_MUT_faz2_yardimci_tok_BASARSA_B3b_A2_KIRMIZI(tmp_path, pano):
    satir = 'oldu "farksal ölçüm: uygulama credential kanalını okuyor (sahte ortamla da 200)"'
    mutant = _degistir(BETIK.read_text(encoding="utf-8"), satir, satir[:-1] + ' [$tok]"')
    kok = _dunya(tmp_path, mutant, "faz1_sonrasi", pano["port"])
    r = _kos(pano, kok, "--faz2")
    kod, _, hata = _sonuc(r)
    assert kod == 0, hata[-300:]
    sizan = _ciktida_jeton(r, _jetonlar(kok))
    assert sizan >= 1, "B3b kör"
    a2, _ = _baski_ihlalleri(mutant)
    assert a2, "A2 kör (yardımcı yazıcı)"


def test_M4_MUT_tee_dev_null_DUSERSE_B3_A2_KIRMIZI(tmp_path, pano):
    satir = "printf '%s\\n' \"$yeni\" | sudo tee \"$KRED\" >/dev/null"
    mutant = _degistir(BETIK.read_text(encoding="utf-8"), satir, satir[:-len(" >/dev/null")])
    kok = _dunya(tmp_path, mutant, "tarihsel", pano["port"])
    r = _kos(pano, kok, "--faz1")
    kod, _, hata = _sonuc(r)
    assert kod == 0, hata[-300:]
    sizan = _ciktida_jeton(r, _jetonlar(kok))
    assert sizan >= 1, "B3 kör (tee)"
    a2, _ = _baski_ihlalleri(mutant)
    assert a2, "A2 kör (tee)"


def test_M5_MUT_okuma_komutu_DUSERSE_B4_KIRMIZI(tmp_path, pano):
    mutant = _degistir(BETIK.read_text(encoding="utf-8"), '  echo "     sudo cat $KRED"\n', "")
    kok = _dunya(tmp_path, mutant, "tarihsel", pano["port"])
    r = _kos(pano, kok, "--faz1")
    kod, _, hata = _sonuc(r)
    assert kod == 0, hata[-300:]
    eksik = _yer_beyani_eksikleri(r, kok)
    assert eksik == ["okuma komutu"]


def test_M6_MUT_davranis_KAYARSA_C_KIRMIZI(tmp_path, pano):
    yeni = BETIK.read_text(encoding="utf-8")
    mutant = _degistir(yeni, 'sudo chmod 0400 "$KRED"', 'sudo chmod 0440 "$KRED"')
    farklar, _ = _farklar(tmp_path, pano, _eski_bicim(yeni), mutant, "tarihsel", "--faz1", {})
    assert farklar == ["imza"], farklar

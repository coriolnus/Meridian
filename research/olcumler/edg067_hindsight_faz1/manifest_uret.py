# EDG-067 korpus paketi: manifest + korpus/ dizini + tar.gz — SALT OKUR, hicbir deftere yazmaz
# Kullanim: python manifest_uret.py <cikti_dizini> [repo_koku]
# Taban kiyasi kill maddesi "AYNI korpus" bu betikle saglanir: ayni tepeden ayni paket cikar.
"""İKİ KİP, TEK ÇIKTI — `.git` VARSA HEAD blob'ları, YOKSA çalışma ağacı + dağıtım damgası.

NEDEN İKİNCİ KİP VAR (ölçüldü, 2026-09-13 08:15:45Z). `hindsight-taban-tazele.service` A1'de
`Result=exit-code` ile düştü: bu betik `git -C /opt/meridian rev-parse HEAD` çağırıyordu ve
A1'de `/opt/meridian/.git` YOK — Ansible dağıtımı (TSK-176, 2026-09-08'den beri) çalışma ağacını
rsync'ler, `.git` gitmez. Son başarılı tazeleme 2026-09-06 (indeks künyesi head_commit ac824e1),
yani `/api/arama` korpusu o günde DONDU ve her Pazar yeniden düşecekti.

KİP ÖLÇÜLEREK SEÇİLİR, tahmin edilmez: `<repo>/.git` VAR MI? (klonda dizin, worktree'de dosya —
`exists()` ikisini de görür.) Git kipinin davranışı bit-özdeş KORUNUR; A1'de disk kipi koşar.

HEAD_COMMIT DİSK KİPİNDE NEREDEN GELİR. `state/dagitim.json`ın `deployed_sha` alanından — o
dosyayı `deploy/ansible/dagit.yml` [B] adımı yazar ve içeriği "bu ağaç HANGİ main tepesinden
rsync'lendi"dir. Damga yoksa, bozuksa ya da `deployed_sha` 40 hanelik küçük-harf sha değilse betik
AÇIK hatayla ÇIKIŞ 2 verir: "bilinmiyor" yazmak (ya da tepeyi tahmin etmek) bayat bir indeksi
taze göstermenin sessiz yoludur ve indeks künyesi provenansın TEK kaydıdır. `state/
belge_esitleme.json`ın `esitlenen_sha`sı BELGE eşitlemesinin sha'sıdır — KOD sha'sı değildir,
burada KULLANILMAZ.

BLOB SHA GİT'SİZ. `sha1(b"blob <bayt>\\0" + içerik)` git'in kendi nesne başlığıdır; sonuç
`git hash-object` ile bit-özdeştir (çivi: `tests/test_edg067_manifest_gitsiz_v481.py`). Blob,
manifest tüketicilerinde üstveri olarak taşınır (`ingest067`, `taban_indeks.manifest_oku`), yani
başka bir sha üretmek provenansı sessizce kırardı.

TEK KAYNAK — `KORPUS_DESENLERI`. Aynı desen listesi hem `git ls-files` pathspec'i hem de disk
taramasının `fnmatch` süzgecidir. İki liste yazılsaydı sessizce ayrışırlardı (tek-kaynak yasası);
eşitlik çiviyle ölçülür. Semantik de ölçüldü: git'in ÖNTANIMLI pathspec'inde (`:(glob)` sihri
YOK) `*` `/` ile sınırlanmaz — `fnmatch` de sınırlamaz; bu depoda iki süzgeç aynı kümeyi veriyor
(105 kart + 161 docs, 2026-09-13).

YASA 6 — `kaynak` ALANININ OKUYUCUSU. Manifest'e eklenen `kaynak` (ve disk kipinde
`dagitildi_utc`) iki yerde okunur: (a) operatör/journalctl — koşum satırı disk kipinde kaynağı
ADIYLA basar; (b) v481 çivileri. Yazan-okuyan zinciri budur; üçüncü bir defter AÇILMAZ.

ÖLÇÜLEMEYEN, ADIYLA: disk kipi çalışma ağacını okur, yani A1'de rsync'in getirdiği ağaçta
izlenmeyen bir `docs/*.md` olsaydı korpusa girerdi (git kipinde giremezdi). Bugünkü dağıtım
temiz-ağaç kapısından geçiyor (`dagit.yml` [0a]) ama bu betik onu DOĞRULAYAMAZ.
"""
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

#: Korpusun sabit iki kalemi + ROADMAP §7 kesitinin KİMLİĞİ (`%23` = `#`; dosya adı DEĞİL).
GUNLUK_YOLU = "MERIDIAN_ENGINEERING_LOG.md"
ROADMAP_YOLU = "ROADMAP.md"
ROADMAP_KESIT_KIMLIGI = "ROADMAP.md%237"

#: DESENLER TEK KAYNAK: git pathspec'i VE disk süzgeci buradan türer. Gruplama SIRAYI taşır
#: (önce kartlar, sonra docs) — manifest sırası tüketicilerin gördüğü sıradır.
KORPUS_DESENLERI = (
    ("research/cards/*.yaml",),          # README.md zaten glob dışı
    ("docs/**/*.md", "docs/*.md"),
)

#: ÜRETİLMİŞ belge — korpus DIŞI, BEYANLI dışlama (elle düzenlenmez, her turda yeniden üretilir;
#: indekse girseydi arama sonucu bir sonraki üretimde sessizce eskirdi).
DISLANAN_YOLLAR = ("docs/RUNBOOK.md",)

#: Dağıtım damgası — `deploy/ansible/dagit.yml` [B] adımının yazdığı dosya.
DAMGA_YOLU = "state/dagitim.json"
SHA40_DESENI = re.compile(r"^[0-9a-f]{40}$")


def hata(mesaj):
    """AÇIK arıza: stderr + çıkış 2. Yarım paket YAZILMAZ, "bilinmiyor" da yazılmaz."""
    print(f"manifest_uret: HATA — {mesaj}", file=sys.stderr)
    raise SystemExit(2)


def blob_sha_hesapla(icerik):
    """`git hash-object -t blob` ile BİT ÖZDEŞ sha1 — git binarisi OLMADAN."""
    return hashlib.sha1(b"blob %d\0" % len(icerik) + icerik).hexdigest()


def desen_koku(desen):
    """Desenin joker İÇERMEYEN önek dizini (`docs/**/*.md` → `docs`). Tarama oradan başlar:
    depo kökünü baştan sona yürümek `.venv`/`ui/node_modules` gibi ağaçları boşuna gezerdi."""
    parcalar = []
    for parca in desen.split("/"):
        if any(joker in parca for joker in "*?["):
            break
        parcalar.append(parca)
    return "/".join(parcalar)


def disk_eslesenler(repo, desenler):
    """Çalışma ağacında `desenler`e uyan yollar (repo köküne göreli, sıralı, tekilleştirilmiş)."""
    repo = Path(repo)
    bulunan = set()
    for desen in desenler:
        kok = repo / desen_koku(desen)
        if not kok.is_dir():
            # Yutma DEĞİL: var olmayan dizinin eşleşme kümesi BOŞtur ve bu görünürdür — eksik
            # korpus tazelemenin terfi kapısında (`taban_terfi.py`, satır oranı ≥ %90) DÜŞER.
            continue
        for dizin, altlar, dosyalar in os.walk(kok):
            altlar[:] = [a for a in altlar if a != ".git"]
            for ad in dosyalar:
                yol = str(Path(dizin, ad).relative_to(repo))
                if fnmatch.fnmatchcase(yol, desen):
                    bulunan.add(yol)
    return sorted(bulunan)


class GitKaynak:
    """`.git` VAR: içerik ve sha HEAD BLOB'undan — 2026-09-13 öncesi davranış, bit-özdeş."""

    ad = "git"

    def __init__(self, repo):
        self.repo = Path(repo)

    def _git(self, *a):
        return subprocess.run(["git", "-C", str(self.repo), *a],
                              capture_output=True, text=True, check=True).stdout

    def head(self):
        return self._git("rev-parse", "HEAD").strip()

    def kunye(self):
        return {}

    def listele(self, grup):
        return sorted(self._git("ls-files", *grup).splitlines())

    def icerik(self, yol):
        return subprocess.run(["git", "-C", str(self.repo), "show", f"HEAD:{yol}"],
                              capture_output=True, check=True).stdout

    def blob(self, yol, icerik):
        return self._git("rev-parse", f"HEAD:{yol}").strip()


class DiskKaynak:
    """`.git` YOK (A1'in rsync'lenmiş ağacı): içerik diskten, sha saf python, tepe DAMGADAN."""

    ad = "dagitim.json"

    def __init__(self, repo):
        self.repo = Path(repo)
        self._damga = self._damga_oku()

    def _damga_oku(self):
        yol = self.repo / DAMGA_YOLU
        if not yol.exists():
            hata(f"`{yol}` YOK ve `{self.repo / '.git'}` de yok — head_commit ÖLÇÜLEMEZ. "
                 "Dağıtım damgası olmadan korpusun provenansı uydurma olurdu; "
                 "dagitim.json'u dağıtım yazar (dagit.yml [B]).")
        try:
            damga = json.loads(yol.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:  # sessiz-yutma: bozuk/okunamayan damga bir hüküm değil ARIZAdır — sebebi adıyla basılır ve betik çıkış 2 ile DURUR (yarım korpus yazılmaz)
            hata(f"`{yol}` okunamadı/ayrıştırılamadı ({e.__class__.__name__}: {e}) — "
                 "dagitim.json bozuk")
        sha = damga.get("deployed_sha")
        if not isinstance(sha, str) or not SHA40_DESENI.match(sha):
            hata(f"`{yol}` içindeki `deployed_sha` 40 haneli küçük-harf sha DEĞİL: {sha!r} — "
                 "tepe ölçülemedi, tahmin edilmeyecek")
        return damga

    def head(self):
        return self._damga["deployed_sha"]

    def kunye(self):
        zaman = self._damga.get("dagitildi_utc")
        if isinstance(zaman, str):
            return {"dagitildi_utc": zaman}
        return {"dagitildi_utc": None,
                "dagitildi_utc_neden": "damgada `dagitildi_utc` yok/metin değil — UYDURULMADI"}

    def listele(self, grup):
        return disk_eslesenler(self.repo, grup)

    def icerik(self, yol):
        return (self.repo / yol).read_bytes()

    def blob(self, yol, icerik):
        return blob_sha_hesapla(icerik)


def kaynak_sec(repo):
    """KİP BURADA ÖLÇÜLÜR: `.git` varlığı (dizin ya da worktree göstergesi dosyası)."""
    return GitKaynak(repo) if (Path(repo) / ".git").exists() else DiskKaynak(repo)


def repo_koku(argv):
    """argv[2] AÇIKÇA verilmemişse cwd'den ölçülür; ölçülemezse tahmin YOK, çıkış 2."""
    if len(argv) > 2:
        return Path(argv[2])
    try:
        return Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                   capture_output=True, text=True, check=True).stdout.strip())
    except (subprocess.CalledProcessError, OSError) as e:  # sessiz-yutma: cwd depo değilse repo kökü ölçülemez; yanlış ağacı paketlemektense DURULUR (arıza adıyla basılır)
        hata(f"repo kökü ölçülemedi ({e.__class__.__name__}) — cwd bir git deposu değil. "
             "Kökü ikinci argümanla AÇIKÇA verin: manifest_uret.py <cikti_dizini> <repo_koku>")


def uret(cikti, repo):
    """Paketi yazar ve koşum satırını basar. Çağıran: `main` (komut satırı sözleşmesi)."""
    cikti, repo = Path(cikti), Path(repo)
    kaynak = kaynak_sec(repo)
    head = kaynak.head()
    korpus = cikti / "korpus"
    dosyalar = []

    def ekle(yol, icerik_bytes, blob):
        hedef = korpus / yol
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_bytes(icerik_bytes)
        dosyalar.append({"yol": yol, "blob": blob, "bayt": len(icerik_bytes)})

    def oku(yol):
        icerik = kaynak.icerik(yol)
        return icerik, kaynak.blob(yol, icerik)

    # 1. Muhendislik gunlugu
    icerik, blob = oku(GUNLUK_YOLU)
    ekle(GUNLUK_YOLU, icerik, blob)

    # 2. ROADMAP §7 kesiti (vaka arsivi bolumu) — document_id kesit kimligi tasir, blob ROADMAP'in
    ham, rm_blob = oku(ROADMAP_YOLU)
    m = re.search(r"^## §7\b.*?(?=^## §8\b|\Z)", ham.decode("utf-8"), re.M | re.S)
    assert m and len(m.group(0)) > 100_000, f"§7 kesiti beklenen boyutta degil: {m and len(m.group(0))}"
    ekle(ROADMAP_KESIT_KIMLIGI, m.group(0).encode("utf-8"), rm_blob)

    # 3-4. Kartlar ve docs — TEK desen kaynagindan, iki kipte ayni kume
    for grup in KORPUS_DESENLERI:
        for yol in kaynak.listele(grup):
            if yol in DISLANAN_YOLLAR:
                continue
            icerik, blob = oku(yol)
            ekle(yol, icerik, blob)

    manifest = {"head_commit": head, "kaynak": kaynak.ad, **kaynak.kunye(), "dosyalar": dosyalar}
    (cikti / "manifest.json").write_text(json.dumps(manifest, indent=1))

    tar_yolu = cikti.parent / "ingest067_paket.tar.gz"
    with tarfile.open(tar_yolu, "w:gz") as t:
        t.add(korpus, arcname="korpus")
        t.add(cikti / "manifest.json", arcname="manifest.json")

    # Git kipinde satır BİÇİMİ 2026-09-13 öncesiyle aynıdır; disk kipi kaynağı ADIYLA ekler.
    ek = "" if kaynak.ad == "git" else f" · kaynak: {kaynak.ad}"
    print(f"HEAD {head[:9]} · {len(dosyalar)} dosya · "
          f"{sum(d['bayt'] for d in dosyalar)//1024} KB{ek} · tar: {tar_yolu}")


def main(argv):
    if len(argv) < 2:
        hata("kullanım: manifest_uret.py <cikti_dizini> [repo_koku]")
    uret(Path(argv[1]), repo_koku(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

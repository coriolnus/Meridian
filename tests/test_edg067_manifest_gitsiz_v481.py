"""test_edg067_manifest_gitsiz_v481.py — EDG-067 korpus paketinin GİT'SİZ (disk) kipi (TSK-186,
2026-09-13).

VAKA (ölçüldü, tahmin edilmedi). `hindsight-taban-tazele.service` 2026-09-13 08:15:45Z
`Result=exit-code` ile düştü: `manifest_uret.py` `git -C /opt/meridian rev-parse HEAD` çağırıyor,
A1'de `/opt/meridian/.git` YOK — Ansible dağıtımı (TSK-176, 2026-09-08'den beri) çalışma ağacını
rsync'ler, `.git` gitmez. Son başarılı tazeleme 2026-09-06 (indeks künyesi head_commit ac824e1);
yani docs arama korpusu o tarihte DONDU ve her Pazar yeniden düşecekti.

SÖZLEŞME (`manifest_uret.py`, komut satırı DEĞİŞMEDİ: `<cikti_dizini> [repo_koku]`):
  * KİP ÖLÇÜLEREK SEÇİLİR: `<repo>/.git` varsa GİT kipi (bugünkü davranış korunur — HEAD
    blob'ları), yoksa DİSK kipi (çalışma ağacı + `state/dagitim.json` sürüm damgası).
  * DİSK kipinde `head_commit` UYDURULMAZ: `state/dagitim.json`daki `deployed_sha` (40 hex)
    okunur; dosya yoksa/alan yoksa/40 hex değilse betik AÇIK hatayla çıkış 2 verir. "bilinmiyor"
    yazmak, bayat bir indeksi taze göstermenin sessiz yoludur.
  * Blob sha'sı git'siz hesaplanır: `sha1(b"blob <bayt>\\0" + içerik)` — `git hash-object` ile
    BİT ÖZDEŞ (çivi ii). Manifest tüketicileri (`taban_indeks.manifest_oku`, `ingest067`) blob'u
    üstveri olarak taşır; başka bir sha üretmek provenansı sessizce kırardı.
  * Dosya listesi TEK KAYNAKTAN türer (`KORPUS_DESENLERI`): git kipinde `git ls-files` pathspec'i,
    disk kipinde aynı desenlerin `fnmatch` karşılığı. İki liste yazılırsa sessizce ayrışır
    (tek-kaynak yasası) — çivi `test_desen_tek_kaynak_git_ve_disk_ayni_kumeyi_verir`.
  * `docs/RUNBOOK.md` ÜRETİLMİŞ belgedir, İKİ kipte de korpus DIŞIdır (beyanlı dışlama).
  * Manifest `kaynak` alanı taşır (`"git"` | `"dagitim.json"`) ve disk kipinde `dagitildi_utc`;
    `head_commit` alanının ADI ve ANLAMI değişmez (tüketiciler onu okur).

YOL-TUTARLI POZİTİF KONTROL (çivi 1-2, kartın kill maddesinin eşi). Tek bir dosya kıyaslamak
portföy-yolu hatalarına kördür: PK AYNI AĞACIN TAMAMINI iki kiple paketler ve `dosyalar`
listesindeki (yol, blob, bayt) ÜÇLÜ KÜMESİNİN ve `head_commit`in BİREBİR eşitliğini ölçer.
Ağaç `git archive HEAD | tar -x` ile tmp'ye çıkarılır — çalışma ağacına DOKUNULMAZ (`git stash`
bu depoda ajan için yasak ve zaten ajanın kendi işini silerdi).

MALİYET BEYANI (bedel yasası): git kipi koşumu bu depoda ~7,8 s sürer (267 dosya × `git show` +
`git rev-parse`). Bu yüzden git kipi MODÜL BAŞINA BİR KEZ koşar (`git_paket` fikstürü) ve altı
çivi aynı çıktıyı okur; her çiviye bir koşum düşseydi dosya tek başına ~1 dakika olurdu.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parent.parent
BETIK = REPO / "research" / "olcumler" / "edg067_hindsight_faz1" / "manifest_uret.py"

#: Betik MODÜL olarak da yüklenebilmelidir: yan etkisiz ithal, `__main__` koruması altında koşum.
#: (Yükleyici `__main__` adını REDDEDER — `ops/sasi_yukleyici._derle`.)
mu = betikten_modul_yukle(BETIK, "manifest_uret_v481")


# =================================================================================================
# YARDIMCILAR
# =================================================================================================
def _kos(cikti, repo=None):
    """Komut satırı SÖZLEŞMESİ koşulur (`main()` değil — ops betiğinin sözleşmesi komut satırıdır)."""
    argv = [sys.executable, str(BETIK), str(cikti)]
    if repo is not None:
        argv.append(str(repo))
    return subprocess.run(argv, capture_output=True, text=True)


def _git(*a, kok=REPO):
    return subprocess.run(["git", "-C", str(kok), *a], capture_output=True, text=True,
                          check=True).stdout


def _manifest(cikti):
    return json.loads((pathlib.Path(cikti) / "manifest.json").read_text(encoding="utf-8"))


def _uclu(manifest):
    return {(d["yol"], d["blob"], d["bayt"]) for d in manifest["dosyalar"]}


HEAD_SHA = _git("rev-parse", "HEAD").strip()


# =================================================================================================
# FİKSTÜRLER — iki kip, AYNI ağaç
# =================================================================================================
@pytest.fixture(scope="module")
def git_paket(tmp_path_factory):
    """GİT kipi, BU worktree'nin HEAD'i. ~7,8 s — modül başına BİR kez."""
    assert (REPO / ".git").exists(), "worktree'de `.git` yok — git kipi ölçülemez"
    cikti = tmp_path_factory.mktemp("v481_git") / "paket"
    r = _kos(cikti, REPO)
    assert r.returncode == 0, f"git kipi düştü: rc={r.returncode}\n{r.stderr}"
    return cikti, r


@pytest.fixture(scope="module")
def agac(tmp_path_factory):
    """HEAD ağacı tmp'de: `git archive HEAD | tar -x`. `.git` YOKTUR → disk kipi.

    Çalışma ağacına dokunulmaz: `git stash` ajan için yasak (ve commit'lenmemiş işi silerdi)."""
    d = tmp_path_factory.mktemp("v481_agac")
    ham = subprocess.run(["git", "-C", str(REPO), "archive", "HEAD"],
                         capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(d)], input=ham, check=True)
    assert not (d / ".git").exists(), "arşiv ağacında `.git` var — disk kipi ölçülemez"
    return d


@pytest.fixture(scope="module")
def disk_paket(agac, tmp_path_factory):
    """DİSK kipi: aynı ağaç + sürüm damgası (`deployed_sha` = HEAD)."""
    (agac / "state").mkdir(exist_ok=True)
    (agac / "state" / "dagitim.json").write_text(
        json.dumps({"deployed_sha": HEAD_SHA, "dagitildi_utc": "2026-09-13T08:15:00Z",
                    "dagitan_host": "pk", "kirli_gec_kullanildi": False}), encoding="utf-8")
    cikti = tmp_path_factory.mktemp("v481_disk") / "paket"
    r = _kos(cikti, agac)
    assert r.returncode == 0, f"disk kipi düştü: rc={r.returncode}\n{r.stderr}"
    return cikti, r


@pytest.fixture()
def bos_agac(tmp_path):
    """`.git`siz, damgasız ağaç — kipin ölçülerek seçildiğini ve hatanın AÇIK olduğunu sınar."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a\n", encoding="utf-8")
    return tmp_path


# =================================================================================================
# 1-2) POZİTİF KONTROL — AYNI AĞAÇ, İKİ KİP, AYNI KÜME
# =================================================================================================
def test_pk_git_ve_disk_kipi_ayni_agacta_ayni_dosya_kumesini_uretir(git_paket, disk_paket):
    g, d = _manifest(git_paket[0]), _manifest(disk_paket[0])
    assert _uclu(g) == _uclu(d), {
        "yalniz_git": sorted(_uclu(g) - _uclu(d))[:5],
        "yalniz_disk": sorted(_uclu(d) - _uclu(g))[:5]}
    assert len(g["dosyalar"]) == len(d["dosyalar"]), "aynı yol iki kez sayılmış olabilir"
    assert [x["yol"] for x in g["dosyalar"]] == [x["yol"] for x in d["dosyalar"]], "SIRA ayrıştı"


def test_pk_head_commit_iki_kipte_esit_ve_gercek_head(git_paket, disk_paket):
    g, d = _manifest(git_paket[0]), _manifest(disk_paket[0])
    assert g["head_commit"] == HEAD_SHA
    assert d["head_commit"] == HEAD_SHA, "disk kipi damgayı okumadı (ya da uydurdu)"


# =================================================================================================
# 3) BLOB SHA — `git hash-object` ile BİT ÖZDEŞ
# =================================================================================================
@pytest.mark.parametrize("icerik", [b"", b"merhaba\n", b"# baslik\n\ngovde\n",
                                    b"\x00\x01\xfe\xff", "Türkçe ş ı ğ\n".encode("utf-8"),
                                    b"x" * 5000])
def test_blob_sha_git_hash_object_ile_ozdes(icerik):
    beklenen = subprocess.run(["git", "hash-object", "--stdin"], input=icerik,
                              capture_output=True, check=True).stdout.decode().strip()
    assert mu.blob_sha_hesapla(icerik) == beklenen
    assert mu.blob_sha_hesapla(icerik) == hashlib.sha1(
        b"blob %d\0" % len(icerik) + icerik).hexdigest()


# =================================================================================================
# 4-5) DAMGA YOKSA/BOZUKSA: AÇIK HATA + ÇIKIŞ 2 (uydurma yasağı)
# =================================================================================================
def test_gitsiz_ve_damgasiz_agac_cikis_2_ve_mesajda_dagitim_json(bos_agac, tmp_path):
    r = _kos(tmp_path / "cikti", bos_agac)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "dagitim.json" in (r.stderr + r.stdout), r.stderr
    assert not (tmp_path / "cikti" / "manifest.json").exists(), "yarım paket yazıldı"


@pytest.mark.parametrize("damga", [
    {"deployed_sha": "abc123"},                          # kısa
    {"deployed_sha": "0" * 39},                          # 39 hex
    {"deployed_sha": "0" * 41},                          # 41 hex
    {"deployed_sha": "g" * 40},                          # hex değil
    {"deployed_sha": "A" * 40},                          # büyük harf — git küçük harf yazar
    {"deployed_sha": ""},                                # boş
    {"deployed_sha": None},                              # null
    {"dagitildi_utc": "2026-09-13T08:15:00Z"},           # alan YOK
])
def test_deployed_sha_40_hex_degilse_cikis_2(bos_agac, tmp_path, damga):
    (bos_agac / "state").mkdir(exist_ok=True)
    (bos_agac / "state" / "dagitim.json").write_text(json.dumps(damga), encoding="utf-8")
    r = _kos(tmp_path / "cikti", bos_agac)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "deployed_sha" in (r.stderr + r.stdout), r.stderr


def test_bozuk_json_damgasi_cikis_2(bos_agac, tmp_path):
    (bos_agac / "state").mkdir(exist_ok=True)
    (bos_agac / "state" / "dagitim.json").write_text("{yarim", encoding="utf-8")
    r = _kos(tmp_path / "cikti", bos_agac)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "dagitim.json" in (r.stderr + r.stdout), r.stderr


def test_repo_koku_olculemezse_acik_hata(tmp_path):
    """argv[2] yok VE cwd bir depo değil → `git rev-parse` düşer; tahmin yerine AÇIK hata."""
    calisma = tmp_path / "depo_disi"
    calisma.mkdir()
    r = subprocess.run([sys.executable, str(BETIK), str(tmp_path / "cikti")],
                       capture_output=True, text=True, cwd=calisma)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "repo" in (r.stderr + r.stdout).lower(), r.stderr


# =================================================================================================
# 6) RUNBOOK İKİ KİPTE DE KORPUS DIŞI (beyanlı dışlama)
# =================================================================================================
def test_runbook_iki_kipte_de_korpus_disi(git_paket, disk_paket):
    for ad, cikti in (("git", git_paket[0]), ("disk", disk_paket[0])):
        yollar = {d["yol"] for d in _manifest(cikti)["dosyalar"]}
        assert "docs/RUNBOOK.md" not in yollar, f"{ad} kipi ÜRETİLMİŞ belgeyi korpusa aldı"
        assert not (pathlib.Path(cikti) / "korpus" / "docs" / "RUNBOOK.md").exists(), ad
        # negatif kontrol: süzgeç docs'un TAMAMINI düşürmüş olmasın
        assert any(y.startswith("docs/") for y in yollar), f"{ad} kipinde hiç docs yok"


# =================================================================================================
# 7) `kaynak` ALANI — provenans İKİ KİPTE DE ADIYLA
# =================================================================================================
def test_manifest_kaynak_alani_iki_kipte_dogru(git_paket, disk_paket):
    g, d = _manifest(git_paket[0]), _manifest(disk_paket[0])
    assert g["kaynak"] == "git"
    assert "dagitildi_utc" not in g, "git kipinde dağıtım damgası YOKTUR (uydurma olurdu)"
    assert d["kaynak"] == "dagitim.json"
    assert d["dagitildi_utc"] == "2026-09-13T08:15:00Z", "damganın saati taşınmadı"


def test_disk_kipi_stdout_kaynagi_soyler_git_kipi_bicimi_korur(git_paket, disk_paket):
    """Git kipi çıktı satırı BİT-BİÇİM olarak korunur (journalctl/rapor okuyucuları);
    disk kipi AYNI satıra kaynağı ekler — hangi damgadan koştuğu logdan okunabilsin."""
    bicim = re.compile(r"^HEAD [0-9a-f]{9} · \d+ dosya · \d+ KB · tar: \S+ingest067_paket\.tar\.gz$")
    g_satir = git_paket[1].stdout.strip()
    assert bicim.match(g_satir), g_satir
    d_satir = disk_paket[1].stdout.strip()
    assert d_satir.startswith(f"HEAD {HEAD_SHA[:9]} · "), d_satir
    assert "kaynak: dagitim.json" in d_satir, d_satir


# =================================================================================================
# 8) GİT KİPİ — BAĞIMSIZ ORACLE (`git ls-tree`), bugünkü davranış DEĞİŞMEDİ
# =================================================================================================
def _ls_tree_oracle():
    """(yol → blob) HEAD ağacından, betiğin kullandığı yoldan BAĞIMSIZ komutla."""
    out = {}
    for satir in _git("ls-tree", "-r", "HEAD").splitlines():
        ust, yol = satir.split("\t", 1)
        _mod, tip, sha = ust.split()
        if tip == "blob":
            out[yol] = sha
    return out


def test_git_kipi_ls_tree_oracle_ile_ozdes(git_paket):
    oracle = _ls_tree_oracle()
    g = _manifest(git_paket[0])
    for kayit in g["dosyalar"]:
        yol = kayit["yol"]
        beklenen = oracle["ROADMAP.md"] if yol == "ROADMAP.md%237" else oracle[yol]
        assert kayit["blob"] == beklenen, yol
    assert g["head_commit"] == HEAD_SHA


def test_korpus_icerigi_manifest_baytiyla_ayni(git_paket, disk_paket):
    """`taban_indeks.korpus_chunklari` kill maddesi: diskteki bayt ≠ manifest baytı → kıyas geçersiz."""
    for cikti in (git_paket[0], disk_paket[0]):
        m = _manifest(cikti)
        for kayit in m["dosyalar"]:
            ham = (pathlib.Path(cikti) / "korpus" / kayit["yol"]).read_bytes()
            assert len(ham) == kayit["bayt"], (cikti, kayit["yol"])
            if kayit["yol"] != mu.ROADMAP_KESIT_KIMLIGI:   # kesitin blob'u ROADMAP'in TAMAMInin
                assert mu.blob_sha_hesapla(ham) == kayit["blob"], kayit["yol"]


def test_tar_cikti_dizininin_UST_dizinine_yazilir(git_paket, disk_paket):
    for cikti, _ in (git_paket, disk_paket):
        assert (pathlib.Path(cikti).parent / "ingest067_paket.tar.gz").exists()


# =================================================================================================
# 9) TEK KAYNAK — desen listesi İKİ KEZ yazılmaz
# =================================================================================================
def test_desen_tek_kaynak_git_ve_disk_ayni_kumeyi_verir(agac):
    """`KORPUS_DESENLERI` tek kaynaktır: git pathspec'i ve disk `fnmatch`i AYNI kümeyi vermeli."""
    for grup in mu.KORPUS_DESENLERI:
        git_kume = set(_git("ls-files", *grup).splitlines())
        disk_kume = set(mu.disk_eslesenler(agac, grup))
        assert git_kume == disk_kume, {"grup": grup,
                                       "yalniz_git": sorted(git_kume - disk_kume)[:5],
                                       "yalniz_disk": sorted(disk_kume - git_kume)[:5]}
        assert git_kume, f"{grup} hiçbir şey eşleşmedi — çivi kör olurdu"


def test_desen_listesi_kaynakta_TEK_kez_gecer():
    """İkinci bir desen listesi (git için ayrı, disk için ayrı) sessizce ayrışırdı."""
    kaynak = BETIK.read_text(encoding="utf-8")
    for desen in ("research/cards/*.yaml", "docs/**/*.md", "docs/*.md"):
        assert kaynak.count(f'"{desen}"') == 1, f"{desen} kaynakta bir kereden fazla yazılı"
    assert kaynak.count('"docs/RUNBOOK.md"') == 1, "dışlama iki yerde"


def test_kip_secimi_git_dizininden_olculur_damgadan_degil(git_paket):
    """Bu worktree'de `state/dagitim.json` YOK ve `.git` bir DOSYA (worktree göstergesi):
    kip yine de GİT seçilmeli — seçim `.git`in VARLIĞIYLA ölçülür."""
    assert not (REPO / "state" / "dagitim.json").exists(), "önkoşul değişti — çivi kör"
    assert _manifest(git_paket[0])["kaynak"] == "git"


def test_damgada_dagitildi_utc_yoksa_None_ve_NEDEN(agac, tmp_path):
    """Uydurma yasağı: ölçülemeyen değer `None` + NEDEN — bugünün saati ya da boş dizge DEĞİL."""
    damga = agac / "state" / "dagitim.json"
    onceki = damga.read_text(encoding="utf-8") if damga.exists() else None
    try:
        damga.write_text(json.dumps({"deployed_sha": HEAD_SHA}), encoding="utf-8")
        cikti = tmp_path / "paket"
        r = _kos(cikti, agac)
        assert r.returncode == 0, r.stderr
        m = _manifest(cikti)
        assert m["head_commit"] == HEAD_SHA, "tepe damgadan okunmalıydı"
        assert m["dagitildi_utc"] is None, m.get("dagitildi_utc")
        assert "dagitildi_utc_neden" in m and m["dagitildi_utc_neden"], m
    finally:
        if onceki is not None:
            damga.write_text(onceki, encoding="utf-8")

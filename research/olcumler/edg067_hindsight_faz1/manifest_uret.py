# EDG-067 korpus paketi: HEAD blob'larindan manifest + korpus/ dizini + tar.gz (yerelde kosar, salt-okunur git)
# Kullanim: python manifest_uret.py <cikti_dizini> [repo_koku]
# Taban kiyasi kill maddesi "AYNI korpus" bu betikle saglanir: ayni HEAD'den ayni paket cikar.
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

CIKTI = Path(sys.argv[1])
REPO = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
    subprocess.run(["git", "rev-parse", "--show-toplevel"],
                   capture_output=True, text=True, check=True).stdout.strip())


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a],
                          capture_output=True, text=True, check=True).stdout


head = git("rev-parse", "HEAD").strip()
korpus = CIKTI / "korpus"
dosyalar = []


def ekle(yol, icerik_bytes, blob):
    hedef = korpus / yol
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_bytes(icerik_bytes)
    dosyalar.append({"yol": yol, "blob": blob, "bayt": len(icerik_bytes)})


def head_icerik(yol):
    return subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{yol}"],
                          capture_output=True, check=True).stdout


def blob_sha(yol):
    return git("rev-parse", f"HEAD:{yol}").strip()


# 1. Muhendislik gunlugu
ekle("MERIDIAN_ENGINEERING_LOG.md", head_icerik("MERIDIAN_ENGINEERING_LOG.md"),
     blob_sha("MERIDIAN_ENGINEERING_LOG.md"))

# 2. ROADMAP §7 kesiti (vaka arsivi bolumu) — document_id kesit kimligi tasir
rm = head_icerik("ROADMAP.md").decode("utf-8")
m = re.search(r"^## §7\b.*?(?=^## §8\b|\Z)", rm, re.M | re.S)
assert m and len(m.group(0)) > 100_000, f"§7 kesiti beklenen boyutta degil: {m and len(m.group(0))}"
ekle("ROADMAP.md%237", m.group(0).encode("utf-8"), blob_sha("ROADMAP.md"))

# 3. research/cards/*.yaml (README.md zaten glob disi)
for yol in sorted(git("ls-files", "research/cards/*.yaml").splitlines()):
    ekle(yol, head_icerik(yol), blob_sha(yol))

# 4. docs/*.md — RUNBOOK.md URETILMIS, korpus DISI (beyanli)
for yol in sorted(git("ls-files", "docs/**/*.md", "docs/*.md").splitlines()):
    if yol == "docs/RUNBOOK.md":
        continue
    ekle(yol, head_icerik(yol), blob_sha(yol))

manifest = {"head_commit": head, "dosyalar": dosyalar}
(CIKTI / "manifest.json").write_text(json.dumps(manifest, indent=1))

tar_yolu = CIKTI.parent / "ingest067_paket.tar.gz"
with tarfile.open(tar_yolu, "w:gz") as t:
    t.add(CIKTI / "korpus", arcname="korpus")
    t.add(CIKTI / "manifest.json", arcname="manifest.json")

print(f"HEAD {head[:9]} · {len(dosyalar)} dosya · "
      f"{sum(d['bayt'] for d in dosyalar)//1024} KB · tar: {tar_yolu}")
